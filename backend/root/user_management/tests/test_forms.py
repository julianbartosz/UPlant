# backend/root/user_management/tests/test_forms.py
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from user_management.models import User, Roles
from user_management.forms import (
    CustomUserCreationForm, 
    CustomUserUpdateForm,
    CustomPasswordChangeForm,
    ProfileForm
)
from user_management.factories import UserFactory, AdminFactory

@pytest.mark.unit
class TestCustomUserCreationForm:
    """Test suite for the CustomUserCreationForm."""
    
    def test_form_has_expected_fields(self):
        """Test that the form has all expected fields."""
        form = CustomUserCreationForm()
        expected_fields = ['email', 'username', 'password1', 'password2', 'zip_code']
        
        for field in expected_fields:
            assert field in form.fields
    
    def test_email_field_required(self):
        """Test that email field is required."""
        form = CustomUserCreationForm(data={
            'username': 'testuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
        })
        
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'This field is required' in str(form.errors['email'])
    
    def test_username_field_required(self):
        """Test that username field is required."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123',
        })
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'This field is required' in str(form.errors['username'])
    
    def test_zip_code_field_optional(self):
        """Test that zip_code field is optional."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
        })
        
        assert form.is_valid(), f"Form errors: {form.errors}"
    
    def test_password_fields_required(self):
        """Test that both password fields are required."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
        })
        
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'password2' in form.errors
    
    def test_passwords_must_match(self):
        """Test that password1 and password2 must match."""
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'securepass123',
            'password2': 'differentpass123',
        })
        
        assert not form.is_valid()
        assert 'password2' in form.errors
        assert "The two password fields didn't match" in str(form.errors['password2'])
    
    def test_email_validation(self):
        """Test email format validation."""
        form = CustomUserCreationForm(data={
            'email': 'not-an-email',
            'username': 'testuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
        })
        
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'Enter a valid email address' in str(form.errors['email'])
    
    def test_zip_code_validation(self):
        """Test zip code validation (if provided)."""
        # Test too short zip code
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'zip_code': '123',  # Too short
        })
        
        assert not form.is_valid()
        assert 'zip_code' in form.errors
        assert 'Ensure this value has at least 5 characters' in str(form.errors['zip_code'])
        
        # Test valid zip code
        form = CustomUserCreationForm(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'zip_code': '12345',  # Valid
        })
        
        assert form.is_valid(), f"Form errors: {form.errors}"
    
    def test_saving_form_creates_user(self, db):
        """Test that saving the form creates a user in the database."""
        form = CustomUserCreationForm(data={
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
            'zip_code': '12345',
        })
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        user = form.save()
        
        # Check user was created with correct data
        assert User.objects.filter(email='newuser@example.com').exists()
        assert user.username == 'newuser'
        assert user.zip_code == '12345'
        assert user.check_password('securepass123')
        assert user.role == Roles.US  # Default role
        assert user.is_active is True
    
    def test_duplicate_email_validation(self, db):
        """Test validation for duplicate email addresses."""
        # Create user first
        UserFactory(email='existing@example.com')
        
        # Try to create another with same email
        form = CustomUserCreationForm(data={
            'email': 'existing@example.com',  # Same email
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'securepass123',
        })
        
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'already exists' in str(form.errors['email'])
    
    def test_duplicate_username_validation(self, db):
        """Test validation for duplicate usernames."""
        # Create user first
        UserFactory(username='existinguser')
        
        # Try to create another with same username
        form = CustomUserCreationForm(data={
            'email': 'new@example.com',
            'username': 'existinguser',  # Same username
            'password1': 'securepass123',
            'password2': 'securepass123',
        })
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'already exists' in str(form.errors['username'])


@pytest.mark.unit
class TestCustomUserUpdateForm:
    """Test suite for the CustomUserUpdateForm."""
    
    def test_form_has_expected_fields(self, db):
        """Test that the form has all expected fields."""
        user = UserFactory()
        form = CustomUserUpdateForm(instance=user)
        expected_fields = ['email', 'username', 'role']
        
        for field in expected_fields:
            assert field in form.fields
        
        # Password should not be in the form
        assert 'password' not in form.fields
    
    def test_email_field_disabled(self, db):
        """Test that email field is disabled."""
        user = UserFactory()
        form = CustomUserUpdateForm(instance=user)
        
        assert form.fields['email'].disabled is True
    
    def test_update_username(self, db):
        """Test updating a user's username."""
        user = UserFactory(username='oldusername')
        form = CustomUserUpdateForm(
            instance=user,
            data={
                'email': user.email,  # Should be unchanged due to disabled field
                'username': 'newusername',
                'role': user.role,
            }
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        updated_user = form.save()
        
        # Check username was updated
        assert updated_user.username == 'newusername'
        
        # Email should remain unchanged even if form value is different
        original_email = user.email
        form = CustomUserUpdateForm(
            instance=user,
            data={
                'email': 'changed@example.com',  # Attempt to change
                'username': 'newusername',
                'role': user.role,
            }
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        updated_user = form.save()
        assert updated_user.email == original_email  # Should be unchanged
    
    def test_update_role(self, db):
        """Test updating a user's role."""
        user = UserFactory(role=Roles.US)
        form = CustomUserUpdateForm(
            instance=user,
            data={
                'email': user.email,
                'username': user.username,
                'role': Roles.MO,  # Change role
            }
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        updated_user = form.save()
        
        # Check role was updated
        assert updated_user.role == Roles.MO
    
    def test_duplicate_username_validation(self, db):
        """Test validation for duplicate usernames."""
        # Create two users
        user1 = UserFactory(username='user1')
        user2 = UserFactory(username='user2')
        
        # Try to update user2 with user1's username
        form = CustomUserUpdateForm(
            instance=user2,
            data={
                'email': user2.email,
                'username': 'user1',  # Same as user1
                'role': user2.role,
            }
        )
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'already exists' in str(form.errors['username'])


@pytest.mark.unit
class TestCustomPasswordChangeForm:
    """Test suite for the CustomPasswordChangeForm."""
    
    def test_form_has_expected_fields(self):
        """Test that the form has all expected fields."""
        form = CustomPasswordChangeForm()
        expected_fields = ['old_password', 'new_password', 'confirm_password']
        
        for field in expected_fields:
            assert field in form.fields
    
    def test_all_fields_required(self):
        """Test that all fields are required."""
        form = CustomPasswordChangeForm(data={})
        
        assert not form.is_valid()
        assert 'old_password' in form.errors
        assert 'new_password' in form.errors
        assert 'confirm_password' in form.errors
    
    def test_password_matching_validation(self):
        """Test validation that new passwords must match."""
        form = CustomPasswordChangeForm(data={
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'different123',
        })
        
        assert not form.is_valid()
        assert 'confirm_password' in form.errors
        assert 'New password and Confirm new password do not match' in form.errors['confirm_password']
    
    def test_form_valid_with_matching_passwords(self):
        """Test form is valid when passwords match."""
        form = CustomPasswordChangeForm(data={
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        
        assert form.is_valid(), f"Form errors: {form.errors}"
    
    def test_clean_method_returns_all_data(self):
        """Test that clean method returns all form data."""
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
        }
        form = CustomPasswordChangeForm(data=data)
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        cleaned_data = form.clean()
        
        # All fields should be present in cleaned data
        assert cleaned_data['old_password'] == 'oldpassword123'
        assert cleaned_data['new_password'] == 'newpassword123'
        assert cleaned_data['confirm_password'] == 'newpassword123'


@pytest.mark.unit
class TestProfileForm:
    """Test suite for the ProfileForm."""
    
    def test_form_has_expected_fields(self):
        """Test that the form has all expected fields."""
        form = ProfileForm()
        expected_fields = ['username', 'zip_code']  # Assuming these are the fields
        
        for field in expected_fields:
            assert field in form.fields
    
    def test_can_update_username(self, db):
        """Test updating a user's username."""
        user = UserFactory(username='oldprofileuser')
        form = ProfileForm(
            instance=user,
            data={
                'username': 'newprofileuser',
                'zip_code': user.zip_code,
            }
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        updated_user = form.save()
        
        # Check username was updated
        assert updated_user.username == 'newprofileuser'
    
    def test_can_update_zip_code(self, db):
        """Test updating a user's zip code."""
        user = UserFactory(zip_code='12345')
        form = ProfileForm(
            instance=user,
            data={
                'username': user.username,
                'zip_code': '54321',  # New zip code
            }
        )
        
        assert form.is_valid(), f"Form errors: {form.errors}"
        updated_user = form.save()
        
        # Check zip code was updated
        assert updated_user.zip_code == '54321'
    
    def test_username_uniqueness_validation(self, db):
        """Test validation for unique username."""
        # Create two users
        user1 = UserFactory(username='profileuser1')
        user2 = UserFactory(username='profileuser2')
        
        # Try to update user2 with user1's username
        form = ProfileForm(
            instance=user2,
            data={
                'username': 'profileuser1',  # Already taken by user1
                'zip_code': user2.zip_code,
            }
        )
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'already taken' in str(form.errors['username']) or 'already exists' in str(form.errors['username'])
    
    def test_zip_code_validation(self, db):
        """Test zip code validation."""
        user = UserFactory()
        
        # Test invalid (too short) zip code
        form = ProfileForm(
            instance=user,
            data={
                'username': user.username,
                'zip_code': '123',  # Too short
            }
        )
        
        assert not form.is_valid()
        assert 'zip_code' in form.errors
        assert 'at least 5 characters' in str(form.errors['zip_code'])