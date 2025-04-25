# backend/root/user_management/tests/test_signals.py

import pytest
from unittest.mock import patch, Mock, call
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
from django.conf import settings
from django.test.utils import override_settings
from django.template.loader import render_to_string
from datetime import timedelta

from user_management.models import User, Roles
from user_management.signals import (
    user_about_to_change,
    user_created_or_updated,
    user_logged_in_callback,
    user_logged_out_callback,
    user_login_failed_callback,
    send_welcome_email,
    send_account_reactivated_email,
    send_email_changed_notification,
    get_from_email,
    get_client_ip,
    create_default_garden
)
from user_management.tests.factories import (
    UserFactory, 
    AdminFactory,
    InactiveUserFactory,
    ModeratorFactory,
    NewUserFactory
)


@pytest.mark.unit
class TestPreSaveSignal:
    """Tests for the user_about_to_change signal (pre_save)."""
    
    def test_track_field_changes(self, db):
        """Test that significant field changes are detected and tracked."""
        # Create a user
        user = UserFactory(email="original@example.com", username="original_user")
        
        # Change fields
        user.email = "new@example.com"
        user.username = "new_user"
        
        # Call the signal handler directly
        user_about_to_change(sender=User, instance=user)
        
        # Check that changes were tracked
        assert hasattr(user, '_changed_fields')
        changed_fields = dict((field[0], (field[1], field[2])) for field in user._changed_fields)
        
        assert 'email' in changed_fields
        assert changed_fields['email'][0] == "original@example.com"
        assert changed_fields['email'][1] == "new@example.com"
        
        assert 'username' in changed_fields
        assert changed_fields['username'][0] == "original_user"
        assert changed_fields['username'][1] == "new_user"
    
    def test_detect_account_activation(self, db):
        """Test that activation is detected when is_active changes from False to True."""
        # Create an inactive user
        user = InactiveUserFactory()
        
        # Activate the user
        user.is_active = True
        
        # Call the signal handler directly
        user_about_to_change(sender=User, instance=user)
        
        # Check that activation was detected
        assert hasattr(user, '_was_activated')
        assert user._was_activated is True
    
    def test_no_detection_when_already_active(self, db):
        """Test that _was_activated is not set when user was already active."""
        # Create an active user
        user = UserFactory(is_active=True)
        
        # Change something else but keep active
        user.username = "new_username"
        
        # Call the signal handler directly
        user_about_to_change(sender=User, instance=user)
        
        # Check that activation flag is not set
        assert not hasattr(user, '_was_activated')
    
    def test_handle_nonexistent_user(self, db):
        """Test handler doesn't crash when user doesn't exist in DB yet."""
        # Create a user without saving to DB
        user = UserFactory.build(pk=999, email="nonexistent@example.com")
        
        # Call signal handler directly (should not raise errors)
        user_about_to_change(sender=User, instance=user)
        
        # No fields should be tracked since the user doesn't exist in DB
        assert not hasattr(user, '_changed_fields')


@pytest.mark.unit
class TestPostSaveSignal:
    """Tests for the user_created_or_updated signal (post_save)."""
    
    @patch('user_management.signals.send_welcome_email')
    @patch('user_management.signals.create_default_garden')
    def test_user_creation(self, mock_create_garden, mock_welcome_email, db):
        """Test that new users get welcome email and default garden."""
        # Create a user (this will trigger the signal)
        user = UserFactory()
        
        # Call the signal handler directly to ensure it's tested
        user_created_or_updated(sender=User, instance=user, created=True)
        
        # Check that welcome email was sent
        mock_welcome_email.assert_called_with(user)
        
        # Check that default garden was created
        mock_create_garden.assert_called_with(user)
    
    @patch('user_management.signals.send_welcome_email')
    @patch('user_management.signals.create_default_garden')
    def test_raw_flag_skips_processing(self, mock_create_garden, mock_welcome_email, db):
        """Test that raw flag (for fixtures) prevents signal processing."""
        user = UserFactory()
        
        # Call with raw=True (fixture loading)
        user_created_or_updated(sender=User, instance=user, created=True, raw=True)
        
        # Nothing should be called
        mock_welcome_email.assert_not_called()
        mock_create_garden.assert_not_called()
    
    @patch('user_management.signals.send_account_reactivated_email')
    def test_account_reactivation_detected(self, mock_reactivation_email, db):
        """Test that account reactivation sends notification."""
        user = UserFactory()
        
        # Set the activation flag (normally set by pre_save)
        user._was_activated = True
        
        # Call the signal handler directly
        user_created_or_updated(sender=User, instance=user, created=False)
        
        # Reactivation email should be sent
        mock_reactivation_email.assert_called_with(user)
    
    @patch('user_management.signals.send_email_changed_notification')
    def test_email_change_notification(self, mock_email_changed, db):
        """Test that changing email sends notification to old address."""
        user = UserFactory(email="new@example.com")
        
        # Set up changed fields (normally set by pre_save)
        user._changed_fields = [('email', 'old@example.com', 'new@example.com')]
        
        # Call the signal handler directly
        user_created_or_updated(sender=User, instance=user, created=False)
        
        # Email change notification should be sent
        mock_email_changed.assert_called_with(user, 'old@example.com')
    
    @patch('user_management.signals.logger')
    def test_exception_handling(self, mock_logger, db):
        """Test that exceptions in the signal handler are caught and logged."""
        user = UserFactory()
        
        # Make the handler raise an exception by setting invalid state
        user._changed_fields = "invalid data format"
        
        # Call should not raise exception
        user_created_or_updated(sender=User, instance=user, created=False)
        
        # Error should be logged
        mock_logger.error.assert_called_once()
        assert "Error in user_created_or_updated signal" in mock_logger.error.call_args[0][0]


@pytest.mark.unit
class TestLoginSignals:
    """Tests for user login-related signals."""
    
    @patch('user_management.signals.get_client_ip')
    @patch('user_management.signals.logger')
    def test_login_tracking(self, mock_logger, mock_get_ip, db):
        """Test that successful logins are tracked with IP and user agent."""
        user = UserFactory()
        request = Mock()
        request.META = {'HTTP_USER_AGENT': 'Test Browser'}
        
        # Mock IP address retrieval
        mock_get_ip.return_value = '192.168.1.1'
        
        # Call the signal handler directly
        user_logged_in_callback(sender=None, request=request, user=user)
        
        # Check that last_login was updated
        assert user.last_login is not None
        
        # Check that login was logged with IP and user agent
        mock_logger.info.assert_called_with(
            f"User {user.email} logged in from 192.168.1.1 using Test Browser"
        )
    
    @patch('user_management.signals.get_client_ip')
    @patch('user_management.signals.logger')
    def test_logout_tracking(self, mock_logger, mock_get_ip, db):
        """Test that logouts are tracked with IP."""
        user = UserFactory()
        request = Mock()
        
        # Mock IP address retrieval
        mock_get_ip.return_value = '192.168.1.1'
        
        # Call the signal handler directly
        user_logged_out_callback(sender=None, request=request, user=user)
        
        # Check that logout was logged with IP
        mock_logger.info.assert_called_with(
            f"User {user.email} logged out from 192.168.1.1"
        )
    
    @patch('user_management.signals.logger')
    def test_failed_login_tracking(self, mock_logger, db):
        """Test that failed login attempts are logged."""
        credentials = {'email': 'test@example.com', 'password': 'wrong'}
        
        # Call the signal handler directly
        user_login_failed_callback(sender=None, credentials=credentials)
        
        # Check that failed attempt was logged
        mock_logger.warning.assert_called_with(
            f"Failed login attempt for test@example.com"
        )
    
    @patch('user_management.signals.logger')
    def test_failed_login_with_username(self, mock_logger, db):
        """Test that failed login attempts with username are logged."""
        credentials = {'username': 'testuser', 'password': 'wrong'}
        
        # Call the signal handler directly
        user_login_failed_callback(sender=None, credentials=credentials)
        
        # Check that failed attempt was logged
        mock_logger.warning.assert_called_with(
            f"Failed login attempt for testuser"
        )
    
    @patch('user_management.signals.logger')
    def test_signal_exception_handling(self, mock_logger, db):
        """Test that exceptions in login signals are caught and logged."""
        # Test login signal
        user = UserFactory()
        request = Mock()
        request.META = {}  # Missing user agent to cause error
        
        # Make get_client_ip raise an exception
        with patch('user_management.signals.get_client_ip', side_effect=Exception("Test error")):
            user_logged_in_callback(sender=None, request=request, user=user)
            
            # Error should be logged
            mock_logger.error.assert_called_once()
            assert "Error in user_logged_in signal" in mock_logger.error.call_args[0][0]
        
        # Reset mock
        mock_logger.reset_mock()
        
        # Test logout signal with exception
        with patch('user_management.signals.get_client_ip', side_effect=Exception("Test error")):
            user_logged_out_callback(sender=None, request=request, user=user)
            
            # Error should be logged
            mock_logger.error.assert_called_once()
            assert "Error in user_logged_out signal" in mock_logger.error.call_args[0][0]
            
        # Reset mock
        mock_logger.reset_mock()
        
        # Test login failed signal with exception
        user_login_failed_callback(sender=None, credentials=None)  # None should cause error
        
        # Error should be logged
        mock_logger.error.assert_called_once()
        assert "Error in user_login_failed signal" in mock_logger.error.call_args[0][0]


@pytest.mark.unit
class TestEmailFunctions:
    """Tests for email notification functions."""
    
    @patch('user_management.signals.send_mail')
    @patch('user_management.signals.render_to_string')
    @patch('user_management.signals.logger')
    def test_welcome_email(self, mock_logger, mock_render, mock_send_mail, db):
        """Test that welcome emails are properly formatted and sent."""
        user = UserFactory(email="welcome@example.com", username="welcome_user")
        
        # Mock template rendering
        mock_render.side_effect = [
            "<h1>Welcome HTML</h1>",  # HTML version
            "Welcome text"            # Plain text version
        ]
        
        # Call the function directly
        send_welcome_email(user)
        
        # Check template context
        template_calls = mock_render.call_args_list
        assert len(template_calls) == 2
        context = template_calls[0][0][1]  # First call, second argument
        assert context['user'] == user
        assert 'app_url' in context
        assert 'help_email' in context
        
        # Check email was sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args[1]
        assert call_args['subject'] == "Welcome to UPlant"
        assert call_args['message'] == "Welcome text"
        assert call_args['html_message'] == "<h1>Welcome HTML</h1>"
        assert call_args['recipient_list'] == ["welcome@example.com"]
    
    @patch('user_management.signals.send_mail')
    @patch('user_management.signals.render_to_string')
    def test_welcome_email_template_fallback(self, mock_render, mock_send_mail, db):
        """Test fallback when templates don't exist."""
        user = UserFactory(username="welcome_user")
        
        # Mock template rendering to return empty strings (templates not found)
        mock_render.return_value = ""
        
        # Call the function directly
        send_welcome_email(user)
        
        # Check email was sent with fallback content
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args[1]
        assert "Welcome to UPlant" in call_args['message']
        assert "welcome_user" in call_args['message']
        assert call_args['html_message'] is None  # No HTML fallback
    
    @patch('user_management.signals.send_mail')
    @patch('user_management.signals.logger')
    def test_welcome_email_error_handling(self, mock_logger, mock_send_mail, db):
        """Test error handling when sending welcome email fails."""
        user = UserFactory()
        
        # Make send_mail raise an exception
        mock_send_mail.side_effect = Exception("Email error")
        
        # Call should not raise exception
        send_welcome_email(user)
        
        # Error should be logged
        mock_logger.error.assert_called_once()
        assert "Failed to send welcome email" in mock_logger.error.call_args[0][0]
    
    @patch('user_management.signals.send_mail')
    def test_account_reactivated_email(self, mock_send_mail, db):
        """Test that account reactivation emails are properly sent."""
        user = UserFactory(email="reactivated@example.com", username="reactivated_user")
        
        # Call the function directly
        send_account_reactivated_email(user)
        
        # Check email was sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args[1]
        assert "Account Has Been Reactivated" in call_args['subject']
        assert call_args['recipient_list'] == ["reactivated@example.com"]
    
    @patch('user_management.signals.send_mail')
    def test_email_changed_notification(self, mock_send_mail, db):
        """Test that email change notifications are sent to the old address."""
        user = UserFactory(email="new@example.com", username="changed_user")
        old_email = "old@example.com"
        
        # Call the function directly
        send_email_changed_notification(user, old_email)
        
        # Check email was sent to old address
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args[1]
        assert "Email Address Has Been Changed" in call_args['subject']
        assert "old@example.com" in call_args['message']
        assert "new@example.com" in call_args['message']
        assert call_args['recipient_list'] == ["old@example.com"]


@pytest.mark.unit
class TestHelperFunctions:
    """Tests for helper functions in signals module."""
    
    @patch('user_management.signals.settings')
    def test_get_from_email_with_setting(self, mock_settings):
        """Test that get_from_email returns the configured email."""
        # Setup mock settings
        mock_settings.DEFAULT_FROM_EMAIL = 'configured@example.com'
        
        # Call the function
        email = get_from_email()
        
        # Check result
        assert email == 'configured@example.com'
    
    def test_get_from_email_default(self):
        """Test that get_from_email returns default when setting is missing."""
        # Call the function (no mock, should use default)
        email = get_from_email()
        
        # Check result
        assert email == 'uplant.notifications@gmail.com'
    
    def test_get_client_ip_with_forwarded(self):
        """Test that get_client_ip extracts IP from X-Forwarded-For header."""
        request = Mock()
        request.META = {'HTTP_X_FORWARDED_FOR': '192.168.1.2, 10.0.0.1'}
        
        # Call the function
        ip = get_client_ip(request)
        
        # Check that first IP in chain is returned
        assert ip == '192.168.1.2'
    
    def test_get_client_ip_without_forwarded(self):
        """Test that get_client_ip falls back to REMOTE_ADDR when no X-Forwarded-For."""
        request = Mock()
        request.META = {'REMOTE_ADDR': '192.168.1.3'}
        
        # Call the function
        ip = get_client_ip(request)
        
        # Check that REMOTE_ADDR is returned
        assert ip == '192.168.1.3'


@pytest.mark.unit
class TestCreateDefaultGarden:
    """Tests for the default garden creation function."""
    
    @patch('gardens.models.Garden.objects.create')
    def test_default_garden_creation(self, mock_create, db):
        """Test that default garden is created with correct attributes."""
        user = UserFactory()
        
        # Mock Garden.objects.create to return a mock garden
        mock_garden = Mock()
        mock_garden.id = 1
        mock_create.return_value = mock_garden
        
        # Call the function
        with patch('services.notification_service.create_welcome_notification', create=True):
            result = create_default_garden(user)
        
        # Check that garden was created with correct attributes
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['user'] == user
        assert call_kwargs['name'] == "My First Garden"
        assert call_kwargs['size_x'] == 10
        assert call_kwargs['size_y'] == 10
        
        # Function should return the created garden
        assert result == mock_garden
    
    @patch('services.notification_service.create_welcome_notification', create=True)
    @patch('gardens.models.Garden.objects.create')
    @patch('plants.models.Plant.objects.filter')
    def test_starter_plant_added(self, mock_filter, mock_create, mock_welcome_notif, db):
        """Test that a starter plant is added to the default garden when available."""
        user = UserFactory()
        
        # Mock Garden creation
        mock_garden = Mock()
        mock_garden.id = 1
        mock_create.return_value = mock_garden
        
        # Mock Plant querying to return a starter plant
        mock_plant = Mock()
        mock_plant_qs = Mock()
        mock_plant_qs.order_by.return_value.first.return_value = mock_plant
        mock_filter.return_value = mock_plant_qs
        
        # Mock GardenLog creation
        with patch('gardens.models.GardenLog.objects.create') as mock_log_create:
            with patch('services.notification_service.create_plant_care_notifications', create=True) as mock_care_notif:
                result = create_default_garden(user)
        
        # Check that starter plant was added
        mock_log_create.assert_called_once()
        log_kwargs = mock_log_create.call_args[1]
        assert log_kwargs['garden'] == mock_garden
        assert log_kwargs['plant'] == mock_plant
        assert log_kwargs['x_coordinate'] == 5  # Center position
        assert log_kwargs['y_coordinate'] == 5  # Center position
    
    @override_settings(SKIP_DEFAULT_GARDEN_CREATION=True)
    def test_skip_garden_creation(self, db):
        """Test that garden creation is skipped when configured in settings."""
        user = UserFactory()
        
        # Call the function
        result = create_default_garden(user)
        
        # Function should return early
        assert result is None
    
    @patch('user_management.signals.logger')
    def test_error_handling(self, mock_logger, db):
        """Test that exceptions during garden creation are caught and logged."""
        user = UserFactory()
        
        # Force an error in garden creation
        with patch('gardens.models.Garden.objects.create', side_effect=Exception("Garden error")):
            result = create_default_garden(user)
        
        # Function should return None on error
        assert result is None
        
        # Error should be logged
        mock_logger.error.assert_called_once()
        assert "Failed to create default garden" in mock_logger.error.call_args[0][0]


@pytest.mark.integration
class TestSignalIntegration:
    """Integration tests for signals working together."""
    
    @patch('user_management.signals.send_welcome_email')
    @patch('user_management.signals.create_default_garden')
    def test_user_creation_triggers_signals(self, mock_create_garden, mock_welcome_email, db):
        """Test that creating a user triggers all expected signals."""
        # This creates a user through the ORM, which should trigger signals
        user = User.objects.create_user(
            email='integration@example.com',
            username='integration_user',
            password='password123'
        )
        
        # Check that welcome email was requested
        mock_welcome_email.assert_called_with(user)
        
        # Check that default garden was requested
        mock_create_garden.assert_called_with(user)
    
    @patch('user_management.signals.send_account_reactivated_email')
    def test_user_activation_triggers_signals(self, mock_reactivation_email, db):
        """Test that reactivating a user triggers email notification."""
        # Create inactive user
        user = InactiveUserFactory()
        
        # Activate the user - should trigger signals
        user.is_active = True
        user.save()
        
        # Check that reactivation email was requested
        mock_reactivation_email.assert_called_once()
    
    @patch('user_management.signals.send_email_changed_notification')
    def test_email_change_triggers_signals(self, mock_email_changed, db):
        """Test that changing email triggers notification."""
        # Create user
        user = UserFactory(email="original@example.com")
        
        # Change email - should trigger signals
        user.email = "changed@example.com"
        user.save()
        
        # Check that email change notification was requested
        mock_email_changed.assert_called_with(user, "original@example.com")
    
    def test_login_signals_integration(self, db):
        """Test that Django's login signal triggers our handler."""
        user = UserFactory()
        request = Mock()
        request.META = {'HTTP_USER_AGENT': 'Test Browser'}
        
        with patch('user_management.signals.logger') as mock_logger:
            # Trigger Django's login signal
            user_logged_in.send(sender=None, request=request, user=user)
            
            # Our signal handler should log the login
            assert mock_logger.info.called
            assert "logged in" in mock_logger.info.call_args[0][0]