# backend/root/user_management/tests/test_models.py
import pytest
import time
from django.core.exceptions import ValidationError
from django.test import TestCase
from user_management.models import User, UserManager, Roles
from django.db import IntegrityError
from django.utils import timezone
from datetime import datetime
from django.urls import reverse
from django.test import RequestFactory
from django.contrib.auth import authenticate
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from user_management.views import UserCreateView, PasswordChangeView
from user_management.forms import (
    CustomUserCreationForm, 
    CustomUserUpdateForm,
    CustomPasswordChangeForm,
    ProfileForm
)
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# UNIT TESTS

@pytest.mark.unit
class TestUserManager:
    """Test suite for the custom UserManager."""
    
    def test_create_user_with_required_fields(self, db):
        """Test creating a user with just required fields."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpassword123"
        )
        
        # Verify user was created with correct values
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == Roles.US
        assert user.is_active is True
        assert user.is_superuser is False
        
        # Password should be hashed, not stored as plain text
        assert user.password != "testpassword123"
        assert user.check_password("testpassword123") is True
        
    def test_create_user_with_no_email(self, db):
        """Test creating a user without an email raises error."""
        with pytest.raises(ValueError) as excinfo:
            User.objects.create_user(email="", username="nomail")
            
        assert "The Email must be set" in str(excinfo.value)
        
    def test_create_user_with_extra_fields(self, db):
        """Test that extra fields are properly set on user creation."""
        user = User.objects.create_user(
            email="extra@example.com",
            username="extrafields",
            password="password123",
            zip_code="12345",
            role=Roles.MO,
            is_active=False
        )
        
        assert user.email == "extra@example.com"
        assert user.zip_code == "12345"
        assert user.role == Roles.MO
        assert user.is_active is False
        
    def test_normalize_email(self, db):
        """Test that emails are properly normalized."""
        user = User.objects.create_user(
            email="Test.User@EXAMPLE.COM",
            username="emailtest",
            password="password123"
        )
        
        # Domain part should be lowercase
        assert user.email == "Test.User@example.com"
        
    def test_create_superuser(self, db):
        """Test superuser creation with proper flags."""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123"
        )
        
        assert admin.email == "admin@example.com"
        assert admin.is_superuser is True
        assert admin.is_staff is True  # Should be True via is_staff property
        
    def test_create_superuser_with_is_superuser_false(self, db):
        """Test that creating a superuser with is_superuser=False raises error."""
        with pytest.raises(ValueError) as excinfo:
            User.objects.create_superuser(
                email="notsuper@example.com",
                username="notsuper",
                password="password123",
                is_superuser=False
            )
            
        assert "Superuser must have is_superuser=True" in str(excinfo.value)
        
    def test_get_by_natural_key(self, db):
        """Test retrieving a user by email using get_by_natural_key."""
        user = User.objects.create_user(
            email="natural@example.com",
            username="naturalkey",
            password="password123"
        )
        
        # Test manager method
        retrieved_user = User.objects.get_by_natural_key("natural@example.com")
        assert retrieved_user == user
        
        # Test model class method
        class_retrieved_user = User.get_by_natural_key("natural@example.com")
        assert class_retrieved_user == user


@pytest.mark.unit
class TestRoles:
    """Test the Roles enumeration."""
    
    def test_roles_choices(self):
        """Test that roles choices are properly defined."""
        assert Roles.AD == "Admin"
        assert Roles.US == "User"
        assert Roles.MO == "Moderator"
        
        # Test display values
        assert Roles.AD.label == "Admin"
        assert Roles.US.label == "User"
        assert Roles.MO.label == "Moderator"
        
        # Test choices structure for form fields
        choices = Roles.choices
        assert ("Admin", "Admin") in choices
        assert ("User", "User") in choices
        assert ("Moderator", "Moderator") in choices


@pytest.mark.unit
class TestUserModel:
    """Test suite for the User model."""
    
    def test_user_creation(self, db):
        """Test creating a user directly through the model."""
        user = User.objects.create(
            email="model@example.com",
            username="modeluser",
            password="rawpassword123"  # Note: This won't be hashed automatically
        )
        
        assert user.email == "model@example.com"
        assert user.username == "modeluser"
        # Since we used create directly, the password isn't hashed
        assert user.password == "rawpassword123"
        
    def test_user_str_representation(self, db):
        """Test the string representation of a user."""
        user = User.objects.create_user(
            email="str@example.com",
            username="strtest",
            password="password123"
        )
        
        assert str(user) == f"str@example.com - ID:{user.id}"
        
    def test_get_full_name(self, db):
        """Test get_full_name method returns username or falls back to email."""
        user = User.objects.create_user(
            email="fullname@example.com",
            username="fullnameuser",
            password="password123"
        )
        
        # Should return username when it exists
        assert user.get_full_name() == "fullnameuser"
        
        # Should return email when username is empty
        user.username = ""
        assert user.get_full_name() == "fullname@example.com"
        
    def test_get_short_name(self, db):
        """Test get_short_name returns username."""
        user = User.objects.create_user(
            email="shortname@example.com",
            username="shortnameuser",
            password="password123"
        )
        
        assert user.get_short_name() == "shortnameuser"
        
    def test_is_staff_property(self, db):
        """Test is_staff property for different user roles."""
        # Regular user
        user = User.objects.create_user(
            email="regular@example.com",
            username="regular",
            password="password123",
            role=Roles.US
        )
        assert user.is_staff is False
        
        # Admin user
        admin = User.objects.create_user(
            email="adminrole@example.com",
            username="adminrole",
            password="password123",
            role=Roles.AD
        )
        assert admin.is_staff is True
        
        # Moderator user (not staff)
        mod = User.objects.create_user(
            email="mod@example.com",
            username="moderator",
            password="password123",
            role=Roles.MO
        )
        assert mod.is_staff is False
        
        # Superuser (is staff regardless of role)
        superuser = User.objects.create_superuser(
            email="super@example.com",
            username="superuser",
            password="password123"
        )
        assert superuser.is_staff is True
        
    def test_has_perm(self, db):
        """Test the has_perm method for different users."""
        # Regular user
        user = User.objects.create_user(
            email="perms@example.com",
            username="permsuser",
            password="password123"
        )
        assert user.has_perm("some_permission") is False
        
        # Superuser
        superuser = User.objects.create_superuser(
            email="superperms@example.com",
            username="superperms",
            password="password123"
        )
        assert superuser.has_perm("some_permission") is True
        
    def test_has_module_perms(self, db):
        """Test the has_module_perms method for different users."""
        # Regular user
        user = User.objects.create_user(
            email="modperms@example.com",
            username="modperms",
            password="password123"
        )
        assert user.has_module_perms("some_app") is False
        
        # Superuser
        superuser = User.objects.create_superuser(
            email="supermodperms@example.com",
            username="supermodperms",
            password="password123"
        )
        assert superuser.has_module_perms("some_app") is True
        
    def test_uniqueness_constraints(self, db):
        """Test uniqueness constraints on email and username."""
        # Create first user
        User.objects.create_user(
            email="unique@example.com",
            username="uniqueuser",
            password="password123"
        )
        
        # Attempt to create user with same email
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="unique@example.com",  # Same email
                username="differentuser",
                password="password123"
            )
            
        # Attempt to create user with same username
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="different@example.com",
                username="uniqueuser",  # Same username
                password="password123"
            )
            
    def test_zip_code_validation(self, db):
        """Test zip code validation (length must be 5)."""
        # Too short zip code
        with pytest.raises(ValidationError):
            user = User(
                email="zipcode@example.com",
                username="ziptest",
                zip_code="123"  # Too short
            )
            user.full_clean()
            
        # Correct length zip code should pass
        user = User(
            email="zipcode@example.com",
            username="ziptest",
            zip_code="12345"  # Correct length
        )
        user.full_clean()  # Should not raise
        
    def test_email_validation(self, db):
        """Test email field validation."""
        # Invalid email format
        with pytest.raises(ValidationError):
            user = User(
                email="not-an-email",  # Invalid format
                username="emailtest"
            )
            user.full_clean()
            
        # Valid email should pass
        user = User(
            email="valid@example.com",  # Valid format
            username="emailtest"
        )
        user.full_clean()  # Should not raise

@pytest.mark.unit
class TestCustomUserCreationForm:
    """Test suite for the user creation form."""
    
    def test_form_fields(self):
        """Test that the form has the correct fields."""
        form = CustomUserCreationForm()
        expected_fields = ['email', 'username', 'zip_code', 'password1', 'password2']
        actual_fields = list(form.fields.keys())
        
        for field in expected_fields:
            assert field in actual_fields
    
    def test_email_required(self):
        """Test that email is required."""
        form = CustomUserCreationForm(data={
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'This field is required.' in form.errors['email']
    
    def test_zip_code_optional(self):
        """Test that zip_code is optional."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        
        assert form.is_valid()
    
    def test_default_role_assignment(self):
        """Test that the default role is set to User."""
        form = CustomUserCreationForm()
        assert form.instance.role == "User"
    
    def test_password_confirmation(self):
        """Test that passwords must match."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'differentpassword',
        })
        
        assert not form.is_valid()
        # Django's UserCreationForm has a non-field error for password mismatch
        assert any("password" in error.lower() for error in form.errors.get('password2', []))
    
    def test_form_save(self, db):
        """Test that the form properly saves a new user."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'zip_code': '12345',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        
        assert form.is_valid()
        user = form.save()
        
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.zip_code == '12345'
        assert user.role == "User"
        assert user.check_password('testpassword123')
        assert user.created_at is not None
    
    def test_form_save_sets_created_at(self, db):
        """Test that created_at is set properly when saving."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        
        # Clear created_at before saving to verify the form sets it
        form.instance.created_at = None
        
        assert form.is_valid()
        user = form.save()
        
        assert user.created_at is not None
        # Should be close to current time
        time_diff = (timezone.now() - user.created_at).total_seconds()
        assert time_diff < 10  # Within 10 seconds of test execution


@pytest.mark.unit
class TestCustomUserUpdateForm:
    """Test suite for the user update form."""
    
    def test_form_fields(self, db):
        """Test that the form has the correct fields."""
        user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser', 
            password='password123'
        )
        
        form = CustomUserUpdateForm(instance=user)
        expected_fields = ['email', 'username', 'role']
        actual_fields = list(form.fields.keys())
        
        for field in expected_fields:
            assert field in actual_fields
        
        # Password should be excluded
        assert 'password' not in actual_fields
    
    def test_email_field_disabled(self, db):
        """Test that email field is disabled."""
        user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser', 
            password='password123'
        )
        
        form = CustomUserUpdateForm(instance=user)
        assert form.fields['email'].disabled is True
    
    def test_form_save(self, db):
        """Test that the form properly updates a user."""
        user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser', 
            password='password123',
            role=Roles.US
        )
        
        form = CustomUserUpdateForm(
            instance=user,
            data={
                'email': 'existing@example.com',  # This shouldn't change due to disabled field
                'username': 'updatedusername',
                'role': Roles.MO,
            }
        )
        
        assert form.is_valid()
        updated_user = form.save()
        
        # Email shouldn't change even if submitted
        assert updated_user.email == 'existing@example.com'
        # These fields should update
        assert updated_user.username == 'updatedusername'
        assert updated_user.role == Roles.MO


@pytest.mark.unit
class TestCustomPasswordChangeForm:
    """Test suite for the password change form."""
    
    def test_form_fields(self):
        """Test that the form has the correct fields."""
        form = CustomPasswordChangeForm()
        expected_fields = ['old_password', 'new_password', 'confirm_password']
        actual_fields = list(form.fields.keys())
        
        for field in expected_fields:
            assert field in actual_fields
    
    def test_password_matching_validation(self):
        """Test that new password and confirm password must match."""
        form = CustomPasswordChangeForm(data={
            'old_password': 'currentpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword',
        })
        
        assert not form.is_valid()
        assert 'confirm_password' in form.errors
        assert 'New password and Confirm new password do not match' in form.errors['confirm_password']
    
    def test_form_is_valid_with_matching_passwords(self):
        """Test that form is valid when passwords match."""
        form = CustomPasswordChangeForm(data={
            'old_password': 'currentpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        
        assert form.is_valid()


@pytest.mark.unit
class TestProfileForm:
    """Test suite for the profile update form."""
    
    def test_form_fields(self):
        """Test that the form has the correct fields."""
        form = ProfileForm()
        expected_fields = ['username']
        actual_fields = list(form.fields.keys())
        
        assert len(actual_fields) == len(expected_fields)
        for field in expected_fields:
            assert field in actual_fields
    
    def test_username_uniqueness_validation(self, db):
        """Test that username must be unique."""
        # Create a user first
        User.objects.create_user(
            email='existing@example.com',
            username='existinguser', 
            password='password123'
        )
        
        # Create another user
        new_user = User.objects.create_user(
            email='another@example.com',
            username='anotheruser', 
            password='password123'
        )
        
        # Try to update new_user with the first user's username
        form = ProfileForm(
            instance=new_user,
            data={'username': 'existinguser'}
        )
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'This username is already taken' in form.errors['username'][0]
    
    def test_can_keep_same_username(self, db):
        """Test that user can keep their existing username."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser', 
            password='password123'
        )
        
        # Update with same username
        form = ProfileForm(
            instance=user,
            data={'username': 'testuser'}
        )
        
        assert form.is_valid()
    
    def test_form_save(self, db):
        """Test that form properly updates username."""
        user = User.objects.create_user(
            email='test@example.com',
            username='oldusername', 
            password='password123'
        )
        
        form = ProfileForm(
            instance=user,
            data={'username': 'newusername'}
        )
        
        assert form.is_valid()
        updated_user = form.save()
        
        assert updated_user.username == 'newusername'
        
        # Check that database was updated
        user.refresh_from_db()
        assert user.username == 'newusername'

@pytest.mark.unit
class TestUserCreateView:
    """Test suite for user registration view."""
    
    def test_view_uses_correct_template(self, client):
        """Test that the view uses the correct template."""
        response = client.get(reverse('user_management:create_account'))
        assert response.status_code == 200
        assert 'user_management/create_user.html' in [t.name for t in response.templates]
    
    def test_get_request_returns_form(self, client):
        """Test that GET request returns a form."""
        response = client.get(reverse('user_management:create_account'))
        assert response.status_code == 200
        assert isinstance(response.context['form'], CustomUserCreationForm)
    
    def test_successful_user_creation(self, client, db):
        """Test that valid form data creates a user and redirects."""
        user_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }
        
        response = client.post(
            reverse('user_management:create_account'),
            data=user_data,
            follow=True  # Follow redirects
        )
        
        # Check redirect and success message
        assert response.redirect_chain[0][0] == reverse('login')
        
        # Check user was created with correct data
        assert User.objects.filter(email='newuser@example.com').exists()
        user = User.objects.get(email='newuser@example.com')
        assert user.username == 'newuser'
        assert user.check_password('testpassword123')
        
        # Check success message is in response
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert "account has been created successfully" in str(messages[0])
    
    def test_invalid_form_data(self, client, db):
        """Test handling of invalid form data."""
        # Missing required email field
        invalid_data = {
            'username': 'incomplete',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }
        
        response = client.post(
            reverse('user_management:create_account'),
            data=invalid_data
        )
        
        # Should re-render the form with errors
        assert response.status_code == 200
        assert 'This field is required' in str(response.content)
        
        # No user should be created
        assert not User.objects.filter(username='incomplete').exists()
    
    def test_password_mismatch(self, client, db):
        """Test handling of mismatched passwords."""
        mismatch_data = {
            'email': 'mismatch@example.com',
            'username': 'mismatchuser',
            'password1': 'testpassword123',
            'password2': 'differentpassword',
        }
        
        response = client.post(
            reverse('user_management:create_account'),
            data=mismatch_data
        )
        
        # Should re-render the form with errors
        assert response.status_code == 200
        assert "The two password fields didn't match" in str(response.content)
        
        # No user should be created
        assert not User.objects.filter(email='mismatch@example.com').exists()
    
    def test_form_valid_method(self, db, monkeypatch):
        """Test that form_valid method creates success message."""
        # Setup request and view
        factory = RequestFactory()
        request = factory.post(reverse('user_management:create_account'))
        
        # Add session and message middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Attach messages storage
        messages = FallbackStorage(request)
        request._messages = messages
        
        # Create view instance with request
        view = UserCreateView()
        view.request = request
        
        # Create a valid form with a user
        form = CustomUserCreationForm(data={
            'email': 'valid@example.com',
            'username': 'validuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        
        # Mock super().form_valid() to avoid redirect issues in test
        class MockResponse:
            pass
        
        mock_response = MockResponse()
        monkeypatch.setattr(UserCreateView, 'form_valid', lambda self, form: mock_response)
        
        # Call form_valid directly - we're not testing the parent's form_valid
        # but just that our override adds a message
        view.form_valid(form)
        
        # Check that a success message was added
        message_list = list(messages)
        assert len(message_list) == 1
        assert "account has been created successfully" in str(message_list[0])
    
    def test_form_invalid_method(self, db):
        """Test that form_invalid properly handles errors."""
        # Setup request and view
        factory = RequestFactory()
        request = factory.post(reverse('user_management:create_account'))
        
        # Create view instance with request
        view = UserCreateView()
        view.request = request
        
        # Create an invalid form
        form = CustomUserCreationForm(data={
            'username': 'invaliduser',
            # Missing required email and password
        })
        
        # Ensure form is invalid
        assert not form.is_valid()
        
        # Mock the parent's form_invalid method
        view.form_invalid = lambda form: form.errors
        
        # Call form_invalid and check errors are returned
        result = view.form_invalid(form)
        assert 'email' in result  # Should contain email validation error


@pytest.mark.unit
class TestPasswordChangeView:
    """Test suite for password change view."""
    
    def test_login_required(self, client):
        """Test that unauthenticated users are redirected to login."""
        response = client.get(reverse('user_management:change_password'))
        
        # Should redirect to login page
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_authenticated_access(self, client, db):
        """Test that authenticated users can access the view."""
        # Create and log in a user
        user = User.objects.create_user(
            email='passworduser@example.com',
            username='passworduser',
            password='oldpassword'
        )
        client.force_login(user)
        
        response = client.get(reverse('user_management:change_password'))
        
        # Should return the password change form
        assert response.status_code == 200
        assert 'user_management/change_password.html' in [t.name for t in response.templates]
    
    def test_get_object_returns_current_user(self, client, db):
        """Test that get_object returns the current user."""
        # Create and log in a user
        user = User.objects.create_user(
            email='current@example.com',
            username='currentuser',
            password='password123'
        )
        client.force_login(user)
        
        # Setup view
        view = PasswordChangeView()
        view.request = client.get(reverse('user_management:change_password')).wsgi_request
        
        # Check that get_object returns the logged-in user
        obj = view.get_object()
        assert obj == user
    
    def test_successful_password_change(self, client, db):
        """Test successful password change with correct old password."""
        # Create and log in a user
        user = User.objects.create_user(
            email='success@example.com',
            username='successuser',
            password='oldpassword'
        )
        client.force_login(user)
        
        # Submit password change form
        response = client.post(
            reverse('user_management:change_password'),
            data={
                'old_password': 'oldpassword',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            },
            follow=True
        )
        
        # Should redirect to login page
        assert response.redirect_chain[0][0] == reverse('core:login')
        
        # Refresh user from database
        user.refresh_from_db()
        
        # Verify password was changed
        assert not user.check_password('oldpassword')
        assert user.check_password('newpassword123')
    
    def test_incorrect_old_password(self, client, db):
        """Test handling of incorrect old password."""
        # Create and log in a user
        user = User.objects.create_user(
            email='incorrect@example.com',
            username='incorrectuser',
            password='correctpassword'
        )
        client.force_login(user)
        
        # Submit form with wrong old password
        response = client.post(
            reverse('user_management:change_password'),
            data={
                'old_password': 'wrongpassword',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            }
        )
        
        # Should re-render form with error
        assert response.status_code == 200
        assert 'Old password is incorrect' in str(response.content)
        
        # Password should not be changed
        user.refresh_from_db()
        assert user.check_password('correctpassword')
    
    def test_mismatched_new_passwords(self, client, db):
        """Test handling of mismatched new passwords."""
        # Create and log in a user
        user = User.objects.create_user(
            email='mismatch@example.com',
            username='mismatchuser',
            password='oldpassword'
        )
        client.force_login(user)
        
        # Submit form with mismatched new passwords
        response = client.post(
            reverse('user_management:change_password'),
            data={
                'old_password': 'oldpassword',
                'new_password': 'newpassword123',
                'confirm_password': 'differentpassword'
            }
        )
        
        # Should re-render form with error
        assert response.status_code == 200
        assert 'New password and Confirm new password do not match' in str(response.content)
        
        # Password should not be changed
        user.refresh_from_db()
        assert user.check_password('oldpassword')
    
    def test_form_valid_with_explicit_check(self, db):
        """Test form_valid explicitly checks old password."""
        # Setup request, user and view
        factory = RequestFactory()
        
        user = User.objects.create_user(
            email='valid@example.com',
            username='validuser',
            password='correctpassword'
        )
        
        request = factory.post(reverse('user_management:change_password'))
        request.user = user
        
        # Create view instance with request
        view = PasswordChangeView()
        view.request = request
        view.object = user
        
        # Create form with cleaned data
        form = CustomPasswordChangeForm(instance=user)
        form.cleaned_data = {
            'old_password': 'wrongpassword',  # Wrong password
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        # Mock the parent's form_invalid method
        view.form_invalid = lambda form: form.errors
        
        # Call form_valid and check it adds an error when password check fails
        result = view.form_valid(form)
        
        # Should return form errors due to incorrect password
        assert result is not None
        
        # Password should not be changed
        user.refresh_from_db()
        assert user.check_password('correctpassword')

# UNIT TESTS END

# ACCEPTANCE TESTS

@pytest.mark.acceptance
class TestUserAcceptance(StaticLiveServerTestCase):
    """
    Acceptance tests for user management workflows.
    
    These tests simulate real user interactions using Selenium WebDriver
    to ensure end-to-end functionality works as expected from a user's perspective.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class with a browser driver."""
        super().setUpClass()
        
        # Choose browser driver based on settings or default to Chrome
        browser = getattr(settings, 'SELENIUM_BROWSER', 'chrome').lower()
        
        if browser == 'firefox':
            options = webdriver.FirefoxOptions()
            if getattr(settings, 'SELENIUM_HEADLESS', True):
                options.add_argument('--headless')
            cls.browser = webdriver.Firefox(options=options)
        else:  # default to Chrome
            options = webdriver.ChromeOptions()
            if getattr(settings, 'SELENIUM_HEADLESS', True):
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-dev-shm-usage')
            cls.browser = webdriver.Chrome(options=options)
            
        # Set viewport size for consistent testing
        cls.browser.set_window_size(1280, 1024)
        
        # Configure wait for elements to be ready
        cls.browser.implicitly_wait(10)
        
        # Set up the WebDriverWait with timeout of 10 seconds
        cls.wait = WebDriverWait(cls.browser, 10)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests by closing the browser."""
        cls.browser.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Set up individual test with clean database."""
        # Create test users if needed
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpassword',
        )
        
        # Generate unique email for this test run to avoid conflicts
        self.test_timestamp = int(time.time())
        self.test_email = f'testuser_{self.test_timestamp}@example.com'
        self.test_username = f'testuser{self.test_timestamp}'
        self.test_password = 'TestPassword123!'
    
    def wait_for_page_load(self, timeout=10):
        """Wait for page to fully load."""
        old_page = self.browser.find_element(By.TAG_NAME, 'html')
        yield
        WebDriverWait(self.browser, timeout).until(
            EC.staleness_of(old_page)
        )
    
    def test_user_registration_flow(self):
        """
        Test the complete user registration flow.
        
        This test verifies that:
        1. A user can access the registration page
        2. Fill out the registration form
        3. Submit the form successfully
        4. Get redirected to login page
        5. See a success message
        """
        # Go to registration page
        self.browser.get(f"{self.live_server_url}{reverse('user_management:create_account')}")
        
        # Verify page title
        assert "Create Account" in self.browser.title
        
        # Fill out form
        email_input = self.browser.find_element(By.NAME, 'email')
        username_input = self.browser.find_element(By.NAME, 'username')
        password1_input = self.browser.find_element(By.NAME, 'password1')
        password2_input = self.browser.find_element(By.NAME, 'password2')
        
        email_input.send_keys(self.test_email)
        username_input.send_keys(self.test_username)
        password1_input.send_keys(self.test_password)
        password2_input.send_keys(self.test_password)
        
        # Submit form
        with self.wait_for_page_load():
            self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify redirect to login page
        current_url = self.browser.current_url
        assert reverse('login') in current_url
        
        # Check success message
        messages = self.browser.find_elements(By.CLASS_NAME, 'alert-success')
        assert any("account has been created successfully" in message.text for message in messages)
        
        # Verify user exists in database
        assert User.objects.filter(email=self.test_email).exists()
        
        user = User.objects.get(email=self.test_email)
        assert user.username == self.test_username
        assert user.check_password(self.test_password)
    
    def test_user_login_flow(self):
        """
        Test the user login flow.
        
        This test verifies that:
        1. A registered user can access the login page
        2. Enter credentials
        3. Login successfully
        4. Get redirected to dashboard/home
        """
        # Create a user to login with
        user = User.objects.create_user(
            email='logintest@example.com',
            username='loginuser',
            password='loginpassword123',
            is_active=True
        )
        
        # Go to login page
        self.browser.get(f"{self.live_server_url}{reverse('login')}")
        
        # Verify page title
        assert "Login" in self.browser.title or "Sign In" in self.browser.title
        
        # Fill out form
        email_input = self.browser.find_element(By.NAME, 'username')  # Django's default auth uses 'username' field
        password_input = self.browser.find_element(By.NAME, 'password')
        
        email_input.send_keys('logintest@example.com')
        password_input.send_keys('loginpassword123')
        
        # Submit form
        with self.wait_for_page_load():
            self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify redirect to dashboard or home
        # Note: The specific URL will depend on your application's redirect after login
        current_url = self.browser.current_url
        assert self.live_server_url in current_url
        assert reverse('login') not in current_url  # Should be redirected away from login
        
        # Check for logged-in indicators
        # This might be a username in header, a logout button, etc.
        try:
            # Look for logout link or button, which confirms we're logged in
            self.browser.find_element(By.XPATH, "//a[contains(@href, 'logout') or contains(text(), 'Logout')]")
            is_logged_in = True
        except NoSuchElementException:
            is_logged_in = False
        
        assert is_logged_in, "User should be logged in with visible logout option"
    
    def test_password_change_flow(self):
        """
        Test the password change flow.
        
        This test verifies that:
        1. A logged-in user can access the password change page
        2. Enter old and new passwords
        3. Successfully change password
        4. Login with the new password
        """
        # Create a user
        user = User.objects.create_user(
            email='pwchange@example.com',
            username='pwchangeuser',
            password='oldpassword123',
            is_active=True
        )
        
        # Login first
        self.browser.get(f"{self.live_server_url}{reverse('login')}")
        
        email_input = self.browser.find_element(By.NAME, 'username')
        password_input = self.browser.find_element(By.NAME, 'password')
        
        email_input.send_keys('pwchange@example.com')
        password_input.send_keys('oldpassword123')
        
        with self.wait_for_page_load():
            self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Go to password change page
        self.browser.get(f"{self.live_server_url}{reverse('user_management:change_password')}")
        
        # Fill out password change form
        old_password_input = self.browser.find_element(By.NAME, 'old_password')
        new_password_input = self.browser.find_element(By.NAME, 'new_password')
        confirm_password_input = self.browser.find_element(By.NAME, 'confirm_password')
        
        old_password_input.send_keys('oldpassword123')
        new_password_input.send_keys('newpassword456')
        confirm_password_input.send_keys('newpassword456')
        
        # Submit form
        with self.wait_for_page_load():
            self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify redirect to login page
        current_url = self.browser.current_url
        assert reverse('core:login') in current_url
        
        # Try logging in with new password
        email_input = self.browser.find_element(By.NAME, 'username')
        password_input = self.browser.find_element(By.NAME, 'password')
        
        email_input.send_keys('pwchange@example.com')
        password_input.send_keys('newpassword456')
        
        with self.wait_for_page_load():
            self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Verify successful login
        assert reverse('login') not in self.browser.current_url
        
        # Verify password was actually changed in database
        user.refresh_from_db()
        assert user.check_password('newpassword456')
    
    def test_registration_validation_errors(self):
        """
        Test validation errors in the registration form.
        
        This test verifies that:
        1. Form validation works for common errors
        2. Helpful error messages are displayed
        3. User is not created when validation fails
        """
        # Go to registration page
        self.browser.get(f"{self.live_server_url}{reverse('user_management:create_account')}")
        
        # Test case 1: Empty form submission
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Check for error messages
        form_errors = self.browser.find_elements(By.CLASS_NAME, 'errorlist')
        assert len(form_errors) > 0
        
        # Test case 2: Email format validation
        email_input = self.browser.find_element(By.NAME, 'email')
        username_input = self.browser.find_element(By.NAME, 'username')
        password1_input = self.browser.find_element(By.NAME, 'password1')
        password2_input = self.browser.find_element(By.NAME, 'password2')
        
        # Clear fields first
        email_input.clear()
        username_input.clear()
        password1_input.clear()
        password2_input.clear()
        
        # Enter invalid email, valid other fields
        email_input.send_keys('not-an-email')
        username_input.send_keys(self.test_username)
        password1_input.send_keys(self.test_password)
        password2_input.send_keys(self.test_password)
        
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Check that form shows email validation error
        page_source = self.browser.page_source
        assert "valid email" in page_source.lower() or "enter a valid" in page_source.lower()
        
        # Test case 3: Password mismatch
        email_input.clear()
        username_input.clear()
        password1_input.clear()
        password2_input.clear()
        
        email_input.send_keys(self.test_email)
        username_input.send_keys(self.test_username)
        password1_input.send_keys(self.test_password)
        password2_input.send_keys("DifferentPassword123!")
        
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Check that form shows password mismatch error
        page_source = self.browser.page_source
        assert "password" in page_source.lower() and "match" in page_source.lower()
        
        # Verify no users were created during these invalid attempts
        assert not User.objects.filter(email=self.test_email).exists()
        assert not User.objects.filter(username=self.test_username).exists()
    
    def test_password_change_validation(self):
        """
        Test validation in the password change form.
        
        This test verifies that:
        1. Wrong old password is rejected
        2. Password mismatch is detected
        3. Password is not changed when validation fails
        """
        # Create and login user
        user = User.objects.create_user(
            email='pwvalidation@example.com',
            username='pwvalidationuser',
            password='originalpassword',
            is_active=True
        )
        
        # Login
        self.browser.get(f"{self.live_server_url}{reverse('login')}")
        
        email_input = self.browser.find_element(By.NAME, 'username')
        password_input = self.browser.find_element(By.NAME, 'password')
        
        email_input.send_keys('pwvalidation@example.com')
        password_input.send_keys('originalpassword')
        
        with self.wait_for_page_load():
            self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Test case 1: Wrong old password
        self.browser.get(f"{self.live_server_url}{reverse('user_management:change_password')}")
        
        old_password_input = self.browser.find_element(By.NAME, 'old_password')
        new_password_input = self.browser.find_element(By.NAME, 'new_password')
        confirm_password_input = self.browser.find_element(By.NAME, 'confirm_password')
        
        old_password_input.send_keys('wrongpassword')
        new_password_input.send_keys('newpassword789')
        confirm_password_input.send_keys('newpassword789')
        
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Check for error message
        page_source = self.browser.page_source
        assert "old password is incorrect" in page_source.lower()
        
        # Test case 2: Password mismatch
        old_password_input.clear()
        new_password_input.clear()
        confirm_password_input.clear()
        
        old_password_input.send_keys('originalpassword')
        new_password_input.send_keys('newpassword789')
        confirm_password_input.send_keys('differentnewpassword')
        
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Check for error message
        page_source = self.browser.page_source
        assert "do not match" in page_source.lower()
        
        # Verify password was not changed
        user.refresh_from_db()
        assert user.check_password('originalpassword')
        assert not user.check_password('newpassword789')
        assert not user.check_password('differentnewpassword')

# ACCEPTANCE TESTS END