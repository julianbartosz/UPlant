# backend/root/user_management/api/tests/test_api.py

import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch, MagicMock
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.socialaccount.models import SocialAccount
from user_management.models import Roles

User = get_user_model()

@pytest.fixture
def api_client():
    """Return an authenticated API client."""
    return APIClient()

@pytest.fixture
def authenticated_client(db, regular_user):
    """Return an authenticated API client."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=regular_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, regular_user

@pytest.fixture
def admin_client(db, admin_user):
    """Return an authenticated admin API client."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, admin_user

@pytest.fixture
def regular_user(db):
    """Create a regular user."""
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='Password123!'
    )
    # Create verified email address
    EmailAddress.objects.create(
        user=user,
        email=user.email,
        verified=True,
        primary=True
    )
    return user

@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    admin = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='AdminPass123!',
        # Remove is_staff - it's a property, not a field
        role=Roles.AD,  # Set the role to Admin instead
        is_superuser=True
    )
    
    # Create verified email address
    EmailAddress.objects.create(
        user=admin,
        email=admin.email,
        verified=True,
        primary=True
    )
    return admin

@pytest.mark.django_db
class TestLoginView:
    """Tests for the LoginView."""
    
    def test_login_successful(self, api_client, regular_user):
        """Test successful login returns token."""
        url = reverse('user_api:api-token-auth')  # Changed to match urls.py
        data = {
            'email': 'testuser@example.com',
            'password': 'Password123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'user_id' in response.data
        assert 'email' in response.data
        assert response.data['email'] == 'testuser@example.com'
        
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials."""
        url = reverse('user_api:api-token-auth')  # Changed to match urls.py
        data = {
            'email': 'wrongemail@example.com',
            'password': 'WrongPass123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_missing_fields(self, api_client):
        """Test login with missing fields."""
        url = reverse('user_api:api-token-auth')  # Changed to match urls.py
        # Missing email
        data = {'password': 'Password123!'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserDeleteView:
    """Tests for the UserDeleteView."""
    
    def test_soft_delete_account(self, authenticated_client):
        """Test soft deleting a user account."""
        client, user = authenticated_client
        url = reverse('user_api:user-delete')
        data = {'password': 'Password123!'}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        # Verify user is deactivated
        user.refresh_from_db()
        assert user.is_active is False
        # Verify token is deleted
        assert not Token.objects.filter(user=user).exists()
        
    def test_soft_delete_wrong_password(self, authenticated_client):
        """Test soft delete with wrong password."""
        client, user = authenticated_client
        url = reverse('user_api:user-delete')
        data = {'password': 'WrongPassword!'}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.is_active is True  # User should still be active
        
    def test_hard_delete_not_allowed(self, authenticated_client, settings):
        """Test hard delete when not allowed by settings."""
        settings.ALLOW_USER_HARD_DELETE = False
        client, user = authenticated_client
        url = reverse('user_api:user-delete')
        data = {'password': 'Password123!'}
        
        response = client.delete(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        user.refresh_from_db()  # Should not raise DoesNotExist
        
    def test_hard_delete_allowed(self, authenticated_client, settings):
        """Test hard delete when allowed by settings."""
        settings.ALLOW_USER_HARD_DELETE = True
        client, user = authenticated_client
        url = reverse('user_api:user-delete')
        data = {'password': 'Password123!'}
        user_id = user.id
        
        response = client.delete(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        # User should be completely deleted
        assert not User.objects.filter(id=user_id).exists()


@pytest.mark.django_db
class TestUserDetailView:
    """Tests for the UserDetailView."""
    
    def test_get_user_details_authenticated(self, authenticated_client):
        """Test getting authenticated user details."""
        client, user = authenticated_client
        url = reverse('user_api:user-detail')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
        assert response.data['email'] == user.email
        
    def test_get_user_details_unauthenticated(self, api_client):
        """Test getting user details without authentication."""
        url = reverse('user_api:user-detail')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestUserProfileView:
    """Tests for the UserProfileView."""
    
    def test_get_user_profile(self, authenticated_client):
        """Test getting user profile."""
        client, user = authenticated_client
        url = reverse('user_api:user-profile')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
        assert response.data['email'] == user.email
        
    @patch('user_management.api.views.get_garden_weather_insights')
    def test_get_user_profile_with_weather(self, mock_weather, authenticated_client):
        """Test getting user profile with weather data."""
        client, user = authenticated_client
        user.zip_code = '12345'
        user.save()
        
        # Mock weather data
        mock_weather.return_value = {
            'current_weather': {'temperature': 25},
            'forecast_summary': 'Sunny',
            'watering_needed': {'should_water': True},
            'frost_warning': {'frost_risk': False, 'min_temperature': 10},
            'extreme_heat_warning': {'extreme_heat': False, 'max_temperature': 30},
            'high_wind_warning': {'high_winds': False, 'max_wind_speed': 15},
        }
        
        url = reverse('user_api:user-profile')
        response = client.get(url, {'include_weather': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'weather_summary' in response.data
        assert response.data['weather_summary']['current_temperature'] == 25
        
    def test_update_user_profile(self, authenticated_client):
        """Test updating user profile."""
        client, user = authenticated_client
        url = reverse('user_api:user-profile')
        data = {
            'username': 'updated_user',
            'zip_code': '54321'
        }
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.username == 'updated_user'
        assert user.zip_code == '54321'

@pytest.mark.django_db
class TestUsernameChangeView:
    """Tests for the UsernameChangeView."""
    
    def test_change_username(self, authenticated_client):
        """Test changing username."""
        client, user = authenticated_client
        url = reverse('user_api:update-username')
        data = {'username': 'newusername'}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'newusername'
        user.refresh_from_db()
        assert user.username == 'newusername'
        
    def test_change_username_duplicate(self, authenticated_client, admin_user):
        """Test changing to a username that already exists."""
        client, user = authenticated_client
        url = reverse('user_api:update-username')
        data = {'username': admin_user.username}  # Already exists
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserWeatherView:
    """Tests for the UserWeatherView."""
    
    @patch('user_management.api.views.get_garden_weather_insights')
    def test_get_weather_data(self, mock_weather, authenticated_client):
        """Test getting weather data for user location."""
        client, user = authenticated_client
        user.zip_code = '12345'
        user.save()
        
        # Mock weather data
        mock_data = {'temperature': 25, 'forecast': 'Sunny'}
        mock_weather.return_value = mock_data
        
        url = reverse('user_api:user-weather')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_data
        
    def test_get_weather_no_zip_code(self, authenticated_client):
        """Test getting weather data when user has no zip code."""
        client, user = authenticated_client
        user.zip_code = ''
        user.save()
        
        url = reverse('user_api:user-weather')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLocationUpdateView:
    """Tests for the UserLocationUpdateView."""
    
    @patch('user_management.api.views.get_garden_weather_insights')
    def test_update_location(self, mock_weather, authenticated_client):
        """Test updating user location."""
        client, user = authenticated_client
        mock_weather.return_value = {'temperature': 25}
        
        url = reverse('user_api:user-location-update')
        data = {'zip_code': '54321'}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'weather' in response.data
        user.refresh_from_db()
        assert user.zip_code == '54321'


@pytest.mark.django_db
class TestPasswordChangeView:
    """Tests for the PasswordChangeView."""
    
    def test_change_password(self, authenticated_client):
        """Test changing password."""
        client, user = authenticated_client
        url = reverse('user_api:password-change')
        data = {
            'current_password': 'Password123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data  # New token issued
        
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password('NewPassword123!')
        
    def test_change_password_wrong_current(self, authenticated_client):
        """Test changing password with wrong current password."""
        client, user = authenticated_client
        url = reverse('user_api:password-change')
        data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordResetRequestView:
    """Tests for the PasswordResetRequestView."""
    
    @patch('django.core.mail.send_mail')  # Changed from 'user_management.api.views.send_mail'
    def test_password_reset_request_existing_email(self, mock_send_mail, api_client, regular_user):
        """Test password reset request with existing email."""
        url = reverse('user_api:password-reset')
        data = {'email': regular_user.email}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        mock_send_mail.assert_called_once()
        
    @patch('django.core.mail.send_mail')  # Changed from 'user_management.api.views.send_mail'
    def test_password_reset_request_nonexistent_email(self, mock_send_mail, api_client):
        """Test password reset request with non-existent email."""
        url = reverse('user_api:password-reset')
        data = {'email': 'nonexistent@example.com'}
        
        response = api_client.post(url, data, format='json')
        
        # Should still return 200 to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK
        mock_send_mail.assert_not_called()


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    """Tests for the PasswordResetConfirmView."""
    
    def test_password_reset_confirm(self, api_client, regular_user):
        """Test confirming password reset."""
        uid = urlsafe_base64_encode(force_bytes(regular_user.pk))
        token = default_token_generator.make_token(regular_user)
        
        url = reverse('user_api:password-reset-confirm')
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'NewResetPass123!',
            'confirm_password': 'NewResetPass123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.check_password('NewResetPass123!')
        
    def test_password_reset_confirm_invalid_token(self, api_client, regular_user):
        """Test confirming password reset with invalid token."""
        uid = urlsafe_base64_encode(force_bytes(regular_user.pk))
        
        url = reverse('user_api:password-reset-confirm')
        data = {
            'uid': uid,
            'token': 'invalid-token',
            'new_password': 'NewResetPass123!',
            'confirm_password': 'NewResetPass123!'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        regular_user.refresh_from_db()
        assert not regular_user.check_password('NewResetPass123!')


@pytest.mark.django_db
class TestEmailVerificationView:
    """Tests for the EmailVerificationView."""
    
    @patch('allauth.account.models.EmailConfirmation.confirm')
    def test_email_verification(self, mock_confirm, api_client):
        """Test email verification with valid key."""
        mock_confirm.return_value = True
        
        # Mock EmailConfirmation.objects.get to return our mock
        with patch('user_management.api.views.EmailConfirmation.objects.get') as mock_get:
            mock_confirmation = MagicMock()
            mock_confirmation.confirm = mock_confirm
            mock_get.return_value = mock_confirmation
            
            url = reverse('user_api:email-verification', kwargs={'key': 'valid-key'})
            response = api_client.get(url)
            
            assert response.status_code == status.HTTP_200_OK
            mock_confirm.assert_called_once()
            
    def test_email_verification_invalid_key(self, api_client):
        """Test email verification with invalid key."""
        # Mock EmailConfirmation.objects.get to raise DoesNotExist
        with patch('user_management.api.views.EmailConfirmation.objects.get') as mock_get:
            mock_get.side_effect = EmailConfirmation.DoesNotExist()
            
            url = reverse('user_api:email-verification', kwargs={'key': 'invalid-key'})
            response = api_client.get(url)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestResendVerificationEmailView:
    """Tests for the ResendVerificationEmailView."""
    
    @patch('user_management.api.views.send_email_confirmation')
    def test_resend_verification_email(self, mock_send, authenticated_client):
        """Test resending verification email."""
        client, user = authenticated_client
        
        # Create unverified email
        unverified_email = 'unverified@example.com'
        EmailAddress.objects.create(user=user, email=unverified_email, verified=False)
        
        url = reverse('user_api:resend-verification')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_send.assert_called_once()
        
    def test_resend_verification_no_unverified_email(self, authenticated_client):
        """Test resending verification email when user has no unverified email."""
        client, user = authenticated_client
        
        # Ensure user only has verified emails
        EmailAddress.objects.filter(user=user, verified=False).delete()
        
        url = reverse('user_api:resend-verification')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestEmailChangeRequestView:
    """Tests for the EmailChangeRequestView."""
    
    def test_email_change_request(self, authenticated_client, monkeypatch):
        """Test requesting email change."""
        client, user = authenticated_client
        
        # Use monkeypatch instead of patch decorator
        mock_send = MagicMock()
        monkeypatch.setattr('allauth.account.utils.send_email_confirmation', mock_send)
        
        # Clean up any existing email with this address to avoid conflicts
        EmailAddress.objects.filter(email='newemail@example.com').delete()
        
        url = reverse('user_api:email-change')
        data = {
                'new_email': 'newemail@example.com',
                'password': 'Password123!'  # Add the password field
        }
        
        response = client.post(url, data, format='json')
        
        # For debugging if this fails again
        if response.status_code != status.HTTP_200_OK:
            print(f"Response content: {response.content.decode()}")
        
        assert response.status_code == status.HTTP_200_OK
        # Check that the email was created
        assert EmailAddress.objects.filter(user=user, email='newemail@example.com').exists()
        
    def test_email_change_request_duplicate(self, authenticated_client):
        """Test requesting change to an email that's already in use."""
        client, user = authenticated_client
        
        # Create another user with the email we want to change to
        User.objects.create_user(
            username='another',
            email='duplicate@example.com',
            password='Password123!'
        )
        EmailAddress.objects.create(
            user=User.objects.get(username='another'),
            email='duplicate@example.com',
            verified=True,
            primary=True
        )
        
        url = reverse('user_api:email-change')
        data = {'new_email': 'duplicate@example.com'}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestEmailListView:
    """Tests for the EmailListView."""
    
    def test_list_emails(self, authenticated_client):
        """Test listing user's emails."""
        client, user = authenticated_client
        
        # Add secondary email
        EmailAddress.objects.create(user=user, email='secondary@example.com', verified=False)
        
        url = reverse('user_api:email-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Primary + secondary
        emails = [email['email'] for email in response.data]
        assert user.email in emails
        assert 'secondary@example.com' in emails


@pytest.mark.django_db
class TestSetPrimaryEmailView:
    """Tests for the SetPrimaryEmailView."""
    
    def test_set_primary_email(self, authenticated_client):
        """Test setting a different email as primary."""
        client, user = authenticated_client
        
        # Add verified secondary email
        secondary_email = 'secondary@example.com'
        EmailAddress.objects.create(
            user=user,
            email=secondary_email,
            verified=True,
            primary=False
        )
        
        url = reverse('user_api:set-primary-email')
        data = {'email': secondary_email}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that primary flag was updated
        assert EmailAddress.objects.get(user=user, email=secondary_email).primary is True
        assert EmailAddress.objects.get(user=user, email=user.email).primary is False
        
        # Check that user.email was updated
        user.refresh_from_db()
        assert user.email == secondary_email
        
    def test_set_primary_email_unverified(self, authenticated_client):
        """Test setting an unverified email as primary."""
        client, user = authenticated_client
        
        # Add unverified secondary email
        secondary_email = 'secondary@example.com'
        EmailAddress.objects.create(
            user=user,
            email=secondary_email,
            verified=False,
            primary=False
        )
        
        url = reverse('user_api:set-primary-email')
        data = {'email': secondary_email}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Email primary status should not change
        assert EmailAddress.objects.get(user=user, email=secondary_email).primary is False


@pytest.mark.django_db
class TestSocialAccountDisconnectView:
    """Tests for the SocialAccountDisconnectView."""
    
    def test_disconnect_social_account(self, authenticated_client):
        """Test disconnecting social account."""
        client, user = authenticated_client
        
        # Create social account
        social_account = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='12345'
        )
        
        url = reverse('user_api:disconnect-social')
        data = {'account_id': social_account.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert not SocialAccount.objects.filter(id=social_account.id).exists()
        
    def test_disconnect_only_auth_method(self, authenticated_client):
        """Test disconnecting the only authentication method."""
        client, user = authenticated_client
        
        # Remove user's password
        user.set_unusable_password()
        user.save()
        
        # Create social account
        social_account = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='12345'
        )
        
        url = reverse('user_api:disconnect-social')
        data = {'account_id': social_account.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Social account should still exist
        assert SocialAccount.objects.filter(id=social_account.id).exists()


@pytest.mark.django_db
class TestSocialAccountListView:
    """Tests for the SocialAccountListView."""
    
    def test_list_social_accounts(self, authenticated_client):
        """Test listing user's social accounts."""
        client, user = authenticated_client
        
        # Create social accounts
        SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='12345',
            extra_data={'name': 'Google User'}
        )
        SocialAccount.objects.create(
            user=user,
            provider='facebook',
            uid='67890',
            extra_data={'name': 'Facebook User'}
        )
        
        url = reverse('user_api:social-accounts')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        providers = [account['provider'] for account in response.data]
        assert 'google' in providers
        assert 'facebook' in providers


@pytest.mark.django_db
class TestAdminUserViewSet:
    """Tests for the AdminUserViewSet."""
    
    def test_list_users_as_admin(self, admin_client):
        """Test admin can list users."""
        client, admin = admin_client
        url = reverse('user_api:admin-user-list')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        
    def test_list_users_as_regular_user(self, authenticated_client):
        """Test regular user cannot access admin endpoints."""
        client, user = authenticated_client
        url = reverse('user_api:admin-user-list')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_create_user_as_admin(self, admin_client):
        """Test admin can create users."""
        client, admin = admin_client
        url = reverse('user_api:admin-user-list')
        data = {
            'username': 'newadminuser',
            'email': 'newadmin@example.com',
            'password': 'AdminPass123!',
            'is_staff': True
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newadminuser').exists()
        
    def test_activate_user(self, admin_client, regular_user):
        """Test activating a user."""
        client, admin = admin_client
        
        # First deactivate the user
        regular_user.is_active = False
        regular_user.save()
        
        url = reverse('user_api:admin-user-activate', args=[regular_user.id])
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.is_active is True
        
    def test_deactivate_user(self, admin_client, regular_user):
        """Test deactivating a user."""
        client, admin = admin_client
        url = reverse('user_api:admin-user-deactivate', args=[regular_user.id])
        
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.is_active is False

    @patch('django.core.mail.send_mail')
    def test_reset_password(self, mock_send, admin_client, regular_user):
        """Test resetting user password as admin."""
        client, admin = admin_client
        url = reverse('user_api:admin-user-reset-password', args=[regular_user.id])
        
        old_password_hash = regular_user.password
        
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_send.assert_called_once()
        
        # Check password was changed
        regular_user.refresh_from_db()
        assert regular_user.password != old_password_hash


@pytest.mark.django_db
class TestAdminStatsView:
    """Tests for the AdminStatsView."""
    
    def test_get_stats_as_admin(self, admin_client):
        """Test admin can get system stats."""
        client, admin = admin_client
        url = reverse('user_api:admin-stats')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data
        assert 'emails' in response.data
        assert 'social' in response.data
        
    def test_get_stats_as_regular_user(self, authenticated_client):
        """Test regular user cannot access admin stats."""
        client, user = authenticated_client
        url = reverse('user_api:admin-stats')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN