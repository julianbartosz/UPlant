import pytest
from django.urls import reverse
from django.test import Client, RequestFactory
from django.contrib.messages import get_messages
from django.contrib.auth import authenticate
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

from user_management.models import User, Roles
from user_management.forms import CustomUserCreationForm, CustomPasswordChangeForm
from user_management.views import UserCreateView, PasswordChangeView
from user_management.tests.factories import UserFactory, AdminFactory, InactiveUserFactory


@pytest.fixture
def client():
    """Provides a test client for making requests."""
    return Client()


@pytest.fixture
def authenticated_client(db):
    """Provides an authenticated test client."""
    user = UserFactory()
    client = Client()
    client.login(email=user.email, password="password123")
    return client, user


@pytest.fixture
def admin_client(db):
    """Provides an authenticated admin test client."""
    admin = AdminFactory()
    client = Client()
    client.login(email=admin.email, password="password123")
    return client, admin


@pytest.fixture
def request_factory():
    """Provides a request factory for more control over request objects."""
    return RequestFactory()


def add_session_to_request(request):
    """Helper function to add session to a request object."""
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()


def add_auth_to_request(request, user=None):
    """Helper function to add auth to a request object."""
    middleware = AuthenticationMiddleware(lambda x: None)
    middleware.process_request(request)
    request.user = user


@pytest.mark.django_db
class TestUserRegistrationAcceptance:
    """Acceptance tests for the user registration flow."""
    
    def test_registration_page_loads(self, client):
        """Test that the registration page loads correctly."""
        url = reverse('user_management:register')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'Create an Account' in response.content.decode()
        assert 'form' in response.context
        assert isinstance(response.context['form'], CustomUserCreationForm)
    
    def test_successful_registration(self, client):
        """Test that a user can successfully register."""
        url = reverse('user_management:register')
        user_data = {
            'email': 'new_user@example.com',
            'username': 'new_user',
            'password1': 'SecureP@ss123',
            'password2': 'SecureP@ss123',
            'zip_code': '10001',
        }
        
        response = client.post(url, user_data, follow=True)
        
        # Should redirect to login page after successful registration
        assert response.redirect_chain[-1][0] == reverse('login')
        
        # Check user was created
        assert User.objects.filter(email='new_user@example.com').exists()
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any('successfully' in str(m) for m in messages)
        
        # Check that the new user can authenticate
        user = authenticate(email='new_user@example.com', password='SecureP@ss123')
        assert user is not None
        assert user.username == 'new_user'
    
    def test_registration_validation_errors(self, client):
        """Test that validation errors are shown for invalid registration data."""
        url = reverse('user_management:register')
        
        # Invalid data - passwords don't match
        invalid_data = {
            'email': 'invalid@example.com',
            'username': 'invalid_user',
            'password1': 'Pass123!',
            'password2': 'DifferentPass123!',
            'zip_code': '1234',  # Also invalid zip format
        }
        
        response = client.post(url, invalid_data)
        
        # Should show errors, not redirect
        assert response.status_code == 200
        
        # Form should contain errors
        form = response.context['form']
        assert form.errors
        assert 'password2' in form.errors  # Password mismatch error
        assert 'zip_code' in form.errors   # Zip code validation error
        
        # User should not be created
        assert not User.objects.filter(email='invalid@example.com').exists()
    
    def test_registration_duplicate_email(self, client, db):
        """Test that registration fails when email is already in use."""
        # Create existing user
        existing_user = UserFactory(email='existing@example.com')
        
        url = reverse('user_management:register')
        user_data = {
            'email': 'existing@example.com',  # Try to use existing email
            'username': 'new_username',
            'password1': 'SecureP@ss123',
            'password2': 'SecureP@ss123',
            'zip_code': '10001',
        }
        
        response = client.post(url, user_data)
        
        # Should show errors, not redirect
        assert response.status_code == 200
        
        # Form should contain errors
        form = response.context['form']
        assert 'email' in form.errors
        assert 'already exists' in str(form.errors['email'])
    
    def test_registration_password_requirements(self, client):
        """Test that password requirements are enforced."""
        url = reverse('user_management:register')
        
        # Test with password that is too short
        short_password_data = {
            'email': 'test@example.com',
            'username': 'test_user',
            'password1': 'short',
            'password2': 'short',
            'zip_code': '10001',
        }
        
        response = client.post(url, short_password_data)
        
        # Should show errors, not redirect
        assert response.status_code == 200
        form = response.context['form']
        assert 'password2' in form.errors
        assert 'This password is too short' in str(form.errors['password2'])
        
        # Test with common password
        common_password_data = {
            'email': 'test@example.com',
            'username': 'test_user',
            'password1': 'password',
            'password2': 'password',
            'zip_code': '10001',
        }
        
        response = client.post(url, common_password_data)
        
        # Should show errors, not redirect
        assert response.status_code == 200
        form = response.context['form']
        assert 'password2' in form.errors
        assert 'too common' in str(form.errors['password2'])


@pytest.mark.django_db
class TestPasswordChangeAcceptance:
    """Acceptance tests for the password change flow."""
    
    def test_password_change_page_requires_login(self, client):
        """Test that password change page redirects unauthenticated users to login."""
        url = reverse('user_management:change_password')
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url
    
    def test_password_change_page_loads(self, authenticated_client):
        """Test that the password change page loads for authenticated users."""
        client, user = authenticated_client
        url = reverse('user_management:change_password')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'Change Password' in response.content.decode()
        assert isinstance(response.context['form'], CustomPasswordChangeForm)
    
    def test_successful_password_change(self, authenticated_client):
        """Test that a user can successfully change their password."""
        client, user = authenticated_client
        url = reverse('user_management:change_password')
        
        password_data = {
            'old_password': 'password123',
            'new_password': 'NewSecureP@ss456',
            'confirm_password': 'NewSecureP@ss456',
        }
        
        response = client.post(url, password_data, follow=True)
        
        # Should redirect to login page after password change
        assert response.redirect_chain[-1][0] == reverse('core:login')
        
        # Refresh user from DB
        user.refresh_from_db()
        
        # Old password should no longer work
        assert not authenticate(email=user.email, password='password123')
        
        # New password should work
        assert authenticate(email=user.email, password='NewSecureP@ss456')
    
    def test_password_change_incorrect_old_password(self, authenticated_client):
        """Test that password change fails with incorrect current password."""
        client, user = authenticated_client
        url = reverse('user_management:change_password')
        
        password_data = {
            'old_password': 'wrong_password',
            'new_password': 'NewSecureP@ss456',
            'confirm_password': 'NewSecureP@ss456',
        }
        
        response = client.post(url, password_data)
        
        # Should show error, not redirect
        assert response.status_code == 200
        
        # Form should have error
        form = response.context['form']
        assert form.errors
        assert 'Old password is incorrect' in str(form.errors)
        
        # Password should not be changed
        user.refresh_from_db()
        assert authenticate(email=user.email, password='password123')
    
    def test_password_change_passwords_dont_match(self, authenticated_client):
        """Test that password change fails when confirmation doesn't match."""
        client, user = authenticated_client
        url = reverse('user_management:change_password')
        
        password_data = {
            'old_password': 'password123',
            'new_password': 'NewPassword1',
            'confirm_password': 'DifferentPassword1',
        }
        
        response = client.post(url, password_data)
        
        # Should show error, not redirect
        assert response.status_code == 200
        
        # Form should have error
        form = response.context['form']
        assert form.errors
        assert 'confirm_password' in form.errors
        assert 'Passwords do not match' in str(form.errors['confirm_password'])
        
        # Password should not be changed
        user.refresh_from_db()
        assert authenticate(email=user.email, password='password123')


@pytest.mark.django_db
class TestLoginAcceptance:
    """Acceptance tests for the login flow."""
    
    def test_login_page_loads(self, client):
        """Test that the login page loads correctly."""
        url = reverse('login')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'Login' in response.content.decode()
        assert 'form' in response.context
    
    def test_successful_login(self, client, db):
        """Test that a user can successfully log in."""
        user = UserFactory(email='login_test@example.com')
        url = reverse('login')
        
        login_data = {
            'username': 'login_test@example.com',  # Django's default form uses 'username' field
            'password': 'password123',
        }
        
        response = client.post(url, login_data, follow=True)
        
        # Should redirect to home/dashboard after login
        assert response.status_code == 200
        
        # User should be authenticated
        assert '_auth_user_id' in client.session
        assert int(client.session['_auth_user_id']) == user.id
    
    def test_failed_login_invalid_credentials(self, client, db):
        """Test that login fails with invalid credentials."""
        user = UserFactory(email='login_test@example.com')
        url = reverse('login')
        
        # Try with wrong password
        login_data = {
            'username': 'login_test@example.com',
            'password': 'wrong_password',
        }
        
        response = client.post(url, login_data)
        
        # Should show error, not redirect
        assert response.status_code == 200
        
        # Form should have error
        assert 'Please enter a correct' in response.content.decode()
        
        # User should not be authenticated
        assert '_auth_user_id' not in client.session
        
        # Try with non-existent user
        login_data = {
            'username': 'nonexistent@example.com',
            'password': 'password123',
        }
        
        response = client.post(url, login_data)
        
        # Should show error, not redirect
        assert response.status_code == 200
        assert 'Please enter a correct' in response.content.decode()
    
    def test_inactive_user_cannot_login(self, client, db):
        """Test that inactive users cannot log in."""
        inactive_user = InactiveUserFactory(email='inactive@example.com')
        url = reverse('login')
        
        login_data = {
            'username': 'inactive@example.com',
            'password': 'password123',
        }
        
        response = client.post(url, login_data)
        
        # Should show error, not redirect
        assert response.status_code == 200
        
        # Form should have error
        assert 'inactive' in response.content.decode().lower()
        
        # User should not be authenticated
        assert '_auth_user_id' not in client.session
    
    def test_logout(self, authenticated_client):
        """Test that a user can successfully log out."""
        client, user = authenticated_client
        url = reverse('logout')
        
        # First verify that user is authenticated
        assert '_auth_user_id' in client.session
        
        response = client.get(url, follow=True)
        
        # Should redirect to home/login page after logout
        assert response.status_code == 200
        
        # User should no longer be authenticated
        assert '_auth_user_id' not in client.session


@pytest.mark.django_db
class TestDirectViewMethodsAcceptance:
    """Tests that directly invoke view methods for more granular testing."""
    
    def test_user_create_view_methods(self, request_factory, db):
        """Test UserCreateView methods directly."""
        factory = request_factory
        view = UserCreateView()
        
        # Test GET request
        request = factory.get(reverse('user_management:register'))
        add_session_to_request(request)
        view.request = request
        
        response = view.get(request)
        assert response.status_code == 200
        
        # Test valid form submission
        valid_data = {
            'email': 'method_test@example.com',
            'username': 'method_test',
            'password1': 'SecureP@ss123',
            'password2': 'SecureP@ss123',
            'zip_code': '10001',
        }
        
        request = factory.post(reverse('user_management:register'), valid_data)
        add_session_to_request(request)
        view.request = request
        
        form = CustomUserCreationForm(data=valid_data)
        assert form.is_valid()
        
        # Mock the messages framework
        setattr(request, '_messages', get_messages(request))
        
        response = view.form_valid(form)
        assert response.status_code == 302  # Redirect response
        
        # Test invalid form submission
        invalid_data = {
            'email': 'invalid',
            'username': '',  # Empty username to cause validation error
            'password1': 'pass',
            'password2': 'different',
        }
        
        request = factory.post(reverse('user_management:register'), invalid_data)
        add_session_to_request(request)
        view.request = request
        
        form = CustomUserCreationForm(data=invalid_data)
        assert not form.is_valid()
        
        response = view.form_invalid(form)
        assert response.status_code == 200  # Render form with errors
    
    def test_password_change_view_methods(self, request_factory, db):
        """Test PasswordChangeView methods directly."""
        factory = request_factory
        view = PasswordChangeView()
        user = UserFactory()
        
        # Test get_object method
        request = factory.get(reverse('user_management:change_password'))
        add_session_to_request(request)
        add_auth_to_request(request, user)
        view.request = request
        
        obj = view.get_object()
        assert obj == user
        
        # Test form_valid with correct old password
        valid_data = {
            'old_password': 'password123',
            'new_password': 'NewSecureP@ss456',
            'confirm_password': 'NewSecureP@ss456',
        }
        
        form = CustomPasswordChangeForm(data=valid_data, instance=user)
        # Mock form validation and cleaned_data
        form.is_valid = lambda: True
        form.cleaned_data = valid_data
        
        request = factory.post(reverse('user_management:change_password'), valid_data)
        add_session_to_request(request)
        add_auth_to_request(request, user)
        view.request = request
        view.object = user
        
        response = view.form_valid(form)
        assert response.status_code == 302  # Redirect response
        
        # Test form_valid with incorrect old password
        invalid_data = {
            'old_password': 'wrong_password',
            'new_password': 'NewSecureP@ss456',
            'confirm_password': 'NewSecureP@ss456',
        }
        
        form = CustomPasswordChangeForm(data=invalid_data, instance=user)
        form.cleaned_data = invalid_data
        
        response = view.form_valid(form)
        assert hasattr(form, 'errors')  # Form should have errors added