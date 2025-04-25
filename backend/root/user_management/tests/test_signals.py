# backend/root/user_management/tests/test_signals.py
import pytest
from unittest.mock import patch, MagicMock, call
from django.test import RequestFactory
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, pre_save

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
    get_client_ip,
    get_from_email,
    create_default_garden
)
from user_management.factories import UserFactory, AdminFactory


@pytest.mark.unit
class TestUserSignals:
    """Test suite for user model signals."""

    @pytest.fixture
    def mock_logger(self):
        """Fixture to mock the logger in signals."""
        with patch('user_management.signals.logger') as mock:
            yield mock

    @pytest.fixture
    def mock_send_mail(self):
        """Fixture to mock Django's send_mail function."""
        with patch('user_management.signals.send_mail') as mock:
            yield mock

    @pytest.fixture
    def mock_render_to_string(self):
        """Fixture to mock template rendering."""
        with patch('user_management.signals.render_to_string') as mock:
            # Return a sample template content
            mock.return_value = "Sample email content"
            yield mock

    @pytest.fixture
    def mock_create_default_garden(self):
        """Fixture to mock default garden creation."""
        with patch('user_management.signals.create_default_garden') as mock:
            yield mock

    @pytest.fixture
    def request_factory(self):
        """Fixture for request factory."""
        return RequestFactory()

    # ==================== PRE-SAVE SIGNAL TESTS ====================
    
    def test_user_about_to_change_tracks_field_changes(self, db):
        """Test that pre_save signal tracks field changes."""
        # Create a user first
        user = UserFactory(
            email="original@example.com",
            username="originalname",
            is_active=True
        )
        
        # Make changes to the user
        user.email = "changed@example.com"
        user.username = "newname"
        
        # Manually call the signal handler
        user_about_to_change(User, user)
        
        # Check that _changed_fields was set
        assert hasattr(user, '_changed_fields')
        
        # Changed fields should include email and username with old and new values
        email_change = None
        username_change = None
        
        for field, old_value, new_value in user._changed_fields:
            if field == 'email':
                email_change = (old_value, new_value)
            elif field == 'username':
                username_change = (old_value, new_value)
        
        assert email_change == ("original@example.com", "changed@example.com")
        assert username_change == ("originalname", "newname")
        
        # _was_activated should not be set since user was already active
        assert not hasattr(user, '_was_activated')

    def test_user_about_to_change_detects_activation(self, db):
        """Test that pre_save signal detects account activation."""
        # Create an inactive user
        user = UserFactory(is_active=False)
        
        # Activate the user
        user.is_active = True
        
        # Manually call the signal handler
        user_about_to_change(User, user)
        
        # Check that _was_activated flag was set
        assert hasattr(user, '_was_activated')
        assert user._was_activated is True

    def test_user_about_to_change_skips_new_users(self, db):
        """Test that pre_save signal skips processing for new users."""
        # Create a user but don't save to DB yet (pk will be None)
        user = User(
            email="new@example.com",
            username="newuser"
        )
        user.pk = None  # Ensure pk is None
        
        # Manually call the signal handler
        user_about_to_change(User, user)
        
        # No attributes should have been set
        assert not hasattr(user, '_changed_fields')
        assert not hasattr(user, '_was_activated')

    # ==================== POST-SAVE SIGNAL TESTS ====================
    
    def test_user_created_sends_welcome_email(self, db, mock_send_mail, mock_create_default_garden, mock_logger):
        """Test that welcome email is sent for new users."""
        # Create a new user
        user = UserFactory()
        
        # Manually call the signal handler with created=True
        user_created_or_updated(User, user, created=True)
        
        # Check that the welcome email was sent
        mock_send_mail.assert_called_once()
        assert mock_send_mail.call_args[0][0] == "Welcome to UPlant"  # Subject
        assert user.email in mock_send_mail.call_args[0][3]  # Recipients
        
        # Check that default garden was created
        mock_create_default_garden.assert_called_once_with(user)
        
        # Check that it was logged
        mock_logger.info.assert_any_call(f"New user created: {user.email}")

    def test_user_created_or_updated_handles_account_reactivation(self, db, mock_send_mail, mock_logger):
        """Test that reactivation email is sent when account is reactivated."""
        # Create user
        user = UserFactory()
        
        # Set _was_activated flag
        user._was_activated = True
        
        # Call signal handler with created=False (update)
        user_created_or_updated(User, user, created=False)
        
        # Check that reactivation email was sent
        mock_send_mail.assert_called_once()
        assert "Reactivated" in mock_send_mail.call_args[0][0]  # Subject contains "Reactivated"
        assert user.email in mock_send_mail.call_args[0][3]  # Recipients

    def test_user_created_or_updated_handles_email_change(self, db, mock_send_mail, mock_logger):
        """Test that email change notification is sent."""
        # Create user
        user = UserFactory(email="new@example.com")
        
        # Set _changed_fields including email change
        old_email = "old@example.com"
        user._changed_fields = [('email', old_email, user.email)]
        
        # Call signal handler with created=False (update)
        user_created_or_updated(User, user, created=False)
        
        # Check that email change notification was sent to old email
        mock_send_mail.assert_called_once()
        assert "Email" in mock_send_mail.call_args[0][0]  # Subject contains "Email"
        assert old_email in mock_send_mail.call_args[0][3]  # Recipients includes old email

    def test_user_created_or_updated_skips_fixture_loading(self, db, mock_send_mail, mock_create_default_garden):
        """Test that signal handler skips processing during fixture loading."""
        # Create a user
        user = UserFactory()
        
        # Call signal handler with raw=True (fixture loading)
        user_created_or_updated(User, user, created=True, raw=True)
        
        # Check that nothing happened
        mock_send_mail.assert_not_called()
        mock_create_default_garden.assert_not_called()

    # ==================== LOGIN/LOGOUT SIGNAL TESTS ====================
    
    def test_user_logged_in_callback(self, db, request_factory, mock_logger):
        """Test that login callback updates last_login and logs activity."""
        # Create a user and request
        user = UserFactory()
        request = request_factory.get('/login')
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Store original last_login
        original_time = user.last_login
        
        # Call signal handler
        user_logged_in_callback(sender=None, request=request, user=user)
        
        # Check that last_login was updated
        assert user.last_login > original_time if original_time else user.last_login is not None
        
        # Check that login was logged with IP and user agent
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert user.email in log_message
        assert '127.0.0.1' in log_message
        assert 'Test Browser' in log_message

    def test_user_logged_out_callback(self, db, request_factory, mock_logger):
        """Test that logout callback logs activity."""
        # Create a user and request
        user = UserFactory()
        request = request_factory.get('/logout')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Call signal handler
        user_logged_out_callback(sender=None, request=request, user=user)
        
        # Check that logout was logged with IP
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert user.email in log_message
        assert '127.0.0.1' in log_message
        assert 'logged out' in log_message

    def test_user_login_failed_callback(self, mock_logger):
        """Test that failed login attempts are logged."""
        # Create credentials
        credentials = {
            'email': 'failed@example.com'
        }
        
        # Call signal handler
        user_login_failed_callback(sender=None, credentials=credentials)
        
        # Check that failed attempt was logged
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        assert 'failed@example.com' in log_message
        assert 'Failed login' in log_message

    def test_user_login_failed_with_username(self, mock_logger):
        """Test failed login logged with username if email not provided."""
        # Create credentials with username instead of email
        credentials = {
            'username': 'faileduser'
        }
        
        # Call signal handler
        user_login_failed_callback(sender=None, credentials=credentials)
        
        # Check that failed attempt was logged with username
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        assert 'faileduser' in log_message

    # ==================== EMAIL FUNCTION TESTS ====================
    
    def test_send_welcome_email(self, db, mock_send_mail, mock_render_to_string, mock_logger):
        """Test welcome email sending with templates."""
        # Create a user
        user = UserFactory()
        
        # Call function directly
        send_welcome_email(user)
        
        # Check that email was sent with correct parameters
        mock_send_mail.assert_called_once()
        assert mock_send_mail.call_args[0][0] == "Welcome to UPlant"  # Subject
        assert mock_send_mail.call_args[0][3] == [user.email]  # Recipients
        assert mock_send_mail.call_args[1]['html_message'] == "Sample email content"  # HTML content
        
        # Check for template rendering
        assert mock_render_to_string.call_count == 2
        html_call = mock_render_to_string.call_args_list[0]
        assert html_call[0][0] == 'user_management/email/welcome_email.html'
        assert 'user' in html_call[0][1]  # Context contains user
        
        # Check activity logged
        mock_logger.info.assert_called_once_with(f"Welcome email sent to {user.email}")

    def test_send_account_reactivated_email(self, db, mock_send_mail, mock_render_to_string, mock_logger):
        """Test account reactivation email sending with templates."""
        # Create a user
        user = UserFactory()
        
        # Call function directly
        send_account_reactivated_email(user)
        
        # Check that email was sent with correct parameters
        mock_send_mail.assert_called_once()
        assert "Reactivated" in mock_send_mail.call_args[0][0]  # Subject
        assert mock_send_mail.call_args[0][3] == [user.email]  # Recipients
        
        # Check for template rendering
        assert mock_render_to_string.call_count == 2
        html_call = mock_render_to_string.call_args_list[0]
        assert html_call[0][0] == 'user_management/email/account_reactivated.html'
        
        # Check activity logged
        mock_logger.info.assert_called_once_with(f"Account reactivation email sent to {user.email}")

    def test_send_email_changed_notification(self, db, mock_send_mail, mock_logger):
        """Test email change notification to old email."""
        # Create a user
        user = UserFactory(email="new@example.com")
        old_email = "old@example.com"
        
        # Call function directly
        send_email_changed_notification(user, old_email)
        
        # Check that email was sent with correct parameters
        mock_send_mail.assert_called_once()
        assert "Email" in mock_send_mail.call_args[0][0]  # Subject
        assert mock_send_mail.call_args[0][3] == [old_email]  # Recipients to old email
        
        # Check message content
        message_body = mock_send_mail.call_args[0][1]
        assert old_email in message_body
        assert user.email in message_body
        
        # Check activity logged
        mock_logger.info.assert_called_once_with(f"Email change notification sent to {old_email}")

    # ==================== HELPER FUNCTION TESTS ====================
    
    def test_get_from_email_with_settings(self, settings):
        """Test get_from_email with custom settings."""
        # Set up settings
        settings.DEFAULT_FROM_EMAIL = 'custom@example.com'
        
        # Call function
        email = get_from_email()
        
        # Check result
        assert email == 'custom@example.com'

    def test_get_from_email_default(self, settings):
        """Test get_from_email falls back to default."""
        # Ensure setting is not defined
        if hasattr(settings, 'DEFAULT_FROM_EMAIL'):
            delattr(settings, 'DEFAULT_FROM_EMAIL')
        
        # Call function
        email = get_from_email()
        
        # Check result uses default
        assert email == 'uplant.notifications@gmail.com'

    def test_get_client_ip_with_forwarded_header(self):
        """Test IP extraction with X-Forwarded-For header."""
        # Create request with X-Forwarded-For
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.2, 10.0.0.1'
        
        # Call function
        ip = get_client_ip(request)
        
        # Should return first IP in the chain
        assert ip == '192.168.1.2'

    def test_get_client_ip_without_forwarded_header(self):
        """Test IP extraction without X-Forwarded-For header."""
        # Create request without X-Forwarded-For
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.3'
        
        # Call function
        ip = get_client_ip(request)
        
        # Should return REMOTE_ADDR
        assert ip == '192.168.1.3'

    # ==================== ACTUAL SIGNAL CONNECTION TESTS ====================
    
    @patch('user_management.signals.send_welcome_email')
    @patch('user_management.signals.create_default_garden')
    def test_post_save_signal_for_new_user(self, mock_create_garden, mock_welcome_email, db):
        """Test that actual post_save signal triggers for new user."""
        # Create a user (which should trigger signal)
        user = User.objects.create_user(
            email="signaltest@example.com",
            username="signaltest",
            password="password123"
        )
        
        # Check that our mocked functions were called by signal
        mock_welcome_email.assert_called_once_with(user)
        mock_create_garden.assert_called_once_with(user)

    @patch('user_management.signals.send_account_reactivated_email')
    def test_post_save_signal_for_reactivation(self, mock_reactivation_email, db):
        """Test that actual post_save signal triggers for activation."""
        # Create an inactive user
        user = UserFactory(is_active=False)
        
        # Activate the user (should trigger signal)
        user.is_active = True
        user.save()
        
        # Check that reactivation email was triggered by signal
        mock_reactivation_email.assert_called_once_with(user)

    @patch('user_management.signals.user_logged_in_callback')
    def test_user_logged_in_signal_connection(self, mock_callback, db):
        """Test that user_logged_in signal is connected to our callback."""
        # Create a user and request
        user = UserFactory()
        request = RequestFactory().get('/')
        
        # Send the signal
        user_logged_in.send(sender=None, request=request, user=user)
        
        # Check our callback was called
        mock_callback.assert_called_once()
        assert mock_callback.call_args[1]['user'] == user
        assert mock_callback.call_args[1]['request'] == request

    @patch('user_management.signals.user_logged_out_callback')
    def test_user_logged_out_signal_connection(self, mock_callback, db):
        """Test that user_logged_out signal is connected to our callback."""
        # Create a user and request
        user = UserFactory()
        request = RequestFactory().get('/')
        
        # Send the signal
        user_logged_out.send(sender=None, request=request, user=user)
        
        # Check our callback was called
        mock_callback.assert_called_once()
        assert mock_callback.call_args[1]['user'] == user
        assert mock_callback.call_args[1]['request'] == request

    # ==================== CREATE DEFAULT GARDEN TESTS ====================
    
    @patch('user_management.signals.Garden')
    @patch('user_management.signals.Plant')
    @patch('user_management.signals.GardenLog')
    def test_create_default_garden(self, mock_garden_log, mock_plant, mock_garden, db, mock_logger):
        """Test creation of default garden for new user."""
        # Set up mocks
        mock_garden_instance = MagicMock()
        mock_garden.objects.create.return_value = mock_garden_instance
        
        mock_plant_instance = MagicMock()
        mock_plant.objects.filter.return_value.order_by.return_value.first.return_value = mock_plant_instance
        
        # Create user
        user = UserFactory()
        
        # Call function
        result = create_default_garden(user)
        
        # Verify garden creation
        mock_garden.objects.create.assert_called_once()
        garden_call = mock_garden.objects.create.call_args[1]
        assert garden_call['user'] == user
        assert garden_call['name'] == "My First Garden"
        assert garden_call['size_x'] == 10
        assert garden_call['size_y'] == 10
        
        # Verify starter plant lookup
        mock_plant.objects.filter.assert_called_once()
        
        # Verify garden log creation
        mock_garden_log.objects.create.assert_called_once()
        garden_log_call = mock_garden_log.objects.create.call_args[1]
        assert garden_log_call['garden'] == mock_garden_instance
        assert garden_log_call['plant'] == mock_plant_instance
        assert garden_log_call['x_coordinate'] == 5
        assert garden_log_call['y_coordinate'] == 5
        
        # Verify result
        assert result == mock_garden_instance
        
        # Verify logging
        mock_logger.info.assert_called_with(f"Default garden created for user {user.email}")

    def test_create_default_garden_respects_skip_setting(self, settings, db):
        """Test that garden creation can be disabled via settings."""
        # Enable skip setting
        settings.SKIP_DEFAULT_GARDEN_CREATION = True
        
        # Create a user
        user = UserFactory()
        
        # Mock Garden model to verify it's not called
        with patch('user_management.signals.Garden') as mock_garden:
            # Call function
            result = create_default_garden(user)
            
            # Verify Garden.objects.create was not called
            mock_garden.objects.create.assert_not_called()
            
            # Result should be None
            assert result is None