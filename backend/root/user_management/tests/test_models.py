# backend/root/user_management/tests/test_models.py

import pytest
import re
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta

from user_management.models import User, Roles, UserManager
from user_management.tests.factories import (
    UserFactory, 
    AdminFactory,
    ModeratorFactory,
    InactiveUserFactory,
    NewUserFactory,
    UserWithActivityFactory,
    create_users_with_different_roles
)


@pytest.mark.unit
class TestUserManager:
    """Test suite for the UserManager class."""
    
    def test_create_user_basic(self, db):
        """Test creating a user with basic attributes."""
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='password123'
        )
        
        assert user.email == 'testuser@example.com'
        assert user.username == 'testuser'
        assert user.check_password('password123')
        assert user.role == Roles.US  # Default role
        assert user.is_active is True
        assert user.is_superuser is False
    
    def test_create_user_with_role(self, db):
        """Test creating a user with a specific role."""
        user = User.objects.create_user(
            email='moderator@example.com',
            username='moderator',
            password='password123',
            role=Roles.MO
        )
        
        assert user.role == Roles.MO
    
    def test_create_user_without_email(self, db):
        """Test creating a user without an email raises ValueError."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email='',
                username='nomail',
                password='password123'
            )
    
    def test_create_superuser(self, db):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass'
        )
        
        assert admin.email == 'admin@example.com'
        assert admin.is_superuser is True
        assert admin.role == Roles.US  # Role not automatically set to Admin
    
    def test_create_superuser_with_is_superuser_false(self, db):
        """Test creating a superuser with is_superuser=False raises ValueError."""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                username='admin',
                password='adminpass',
                is_superuser=False
            )
    
    def test_get_by_natural_key(self, db):
        """Test retrieving a user by email using natural key method."""
        user = UserFactory(email='natural@example.com')
        
        # Test manager method
        retrieved = User.objects.get_by_natural_key('natural@example.com')
        assert retrieved == user
        
        # Test class method
        retrieved = User.get_by_natural_key('natural@example.com')
        assert retrieved == user
    
    def test_normalize_email(self, db):
        """Test that emails are normalized (lowercase domain)."""
        # Create a user with mixed case domain
        user = User.objects.create_user(
            email='test@ExAmPlE.CoM',
            username='mixedcase',
            password='password123'
        )
        
        # Check that the domain part is lowercased
        assert user.email == 'test@example.com'


@pytest.mark.unit
class TestRoles:
    """Test suite for the Roles enumeration."""
    
    def test_roles_values(self):
        """Test that Roles enum contains expected values."""
        assert Roles.AD == "Admin"
        assert Roles.US == "User"
        assert Roles.MO == "Moderator"
    
    def test_roles_choices(self):
        """Test that Roles.choices provides pairs of (value, display_name)."""
        choices = dict(Roles.choices)
        assert choices["Admin"] == "Admin"
        assert choices["User"] == "User"
        assert choices["Moderator"] == "Moderator"
    
    def test_user_role_assignment(self, db):
        """Test that roles can be assigned to users."""
        admin = UserFactory(role=Roles.AD)
        user = UserFactory(role=Roles.US)
        moderator = UserFactory(role=Roles.MO)
        
        assert admin.role == "Admin"
        assert user.role == "User"
        assert moderator.role == "Moderator"


@pytest.mark.unit
class TestUserModelBasic:
    """Test basic functionality of the User model."""
    
    def test_user_creation(self, db):
        """Test creating a user with factory."""
        user = UserFactory()
        
        # Check that it was saved to DB with ID
        assert user.id is not None
        assert user.email is not None
        assert user.username is not None
    
    def test_string_representation(self, db):
        """Test the string representation of a User."""
        user = UserFactory(email="test@example.com")
        
        assert str(user) == f"test@example.com - ID:{user.id}"
    
    def test_unique_email_constraint(self, db):
        """Test that email must be unique."""
        UserFactory(email="duplicate@example.com")
        
        # Try to create another user with the same email
        with pytest.raises(IntegrityError):
            UserFactory(email="duplicate@example.com")
    
    def test_unique_username_constraint(self, db):
        """Test that username must be unique."""
        UserFactory(username="duplicate_user")
        
        # Try to create another user with the same username
        with pytest.raises(IntegrityError):
            UserFactory(username="duplicate_user")
    
    def test_email_validation(self, db):
        """Test that invalid emails are rejected."""
        # Invalid email format
        with pytest.raises(ValidationError):
            user = UserFactory.build(email="not-an-email")
            user.full_clean()
    
    def test_zip_code_validation(self, db):
        """Test that zip code must be 5 digits."""
        # Zip code too short
        with pytest.raises(ValidationError):
            user = UserFactory.build(zip_code="123")
            user.full_clean()
        
        # Valid zip code
        user = UserFactory(zip_code="12345")
        user.full_clean()  # Should not raise
    
    def test_timestamps_auto_set(self, db):
        """Test that timestamps are automatically set on creation."""
        user = UserFactory()
        
        assert user.created_at is not None
        assert user.updated_at is not None
        
        # Timestamps should be close to now
        now = timezone.now()
        assert (now - user.created_at).total_seconds() < 10
        assert (now - user.updated_at).total_seconds() < 10
    
    def test_updated_at_auto_update(self, db):
        """Test that updated_at is automatically updated."""
        user = UserFactory()
        original_updated_at = user.updated_at
        
        # Wait a moment to ensure the timestamp changes
        import time
        time.sleep(0.1)
        
        # Update the user
        user.username = "modified_username"
        user.save()
        
        assert user.updated_at > original_updated_at


@pytest.mark.unit
class TestUserAuthentication:
    """Test authentication-related functionality of the User model."""
    
    def test_authentication_success(self, db):
        """Test that users can authenticate with correct credentials."""
        user = UserFactory(
            email="auth@example.com",
            password="correct_password"
        )
        
        # Authenticate with correct credentials
        authenticated = authenticate(
            email="auth@example.com",
            password="correct_password"
        )
        
        assert authenticated is not None
        assert authenticated.id == user.id
    
    def test_authentication_wrong_password(self, db):
        """Test that authentication fails with incorrect password."""
        UserFactory(
            email="auth@example.com",
            password="correct_password"
        )
        
        # Try to authenticate with wrong password
        authenticated = authenticate(
            email="auth@example.com",
            password="wrong_password"
        )
        
        assert authenticated is None
    
    def test_authentication_inactive_user(self, db):
        """Test that inactive users cannot authenticate."""
        InactiveUserFactory(
            email="inactive@example.com",
            password="password123"
        )
        
        # Try to authenticate as inactive user
        authenticated = authenticate(
            email="inactive@example.com",
            password="password123"
        )
        
        assert authenticated is None
    
    def test_password_hashing(self, db):
        """Test that passwords are properly hashed."""
        user = UserFactory(password="test_password")
        
        # Password should be hashed, not stored in plaintext
        assert user.password != "test_password"
        assert user.password.startswith("pbkdf2_sha256$")  # Django's default hasher
        
        # Should be able to check password
        assert user.check_password("test_password")
        assert not user.check_password("wrong_password")


@pytest.mark.unit
class TestUserPermissions:
    """Test permission-related functionality of the User model."""
    
    def test_is_staff_property(self, db):
        """Test that is_staff property returns correctly based on role."""
        admin = AdminFactory()
        moderator = ModeratorFactory()
        user = UserFactory()
        
        assert admin.is_staff is True
        assert moderator.is_staff is False
        assert user.is_staff is False
        
        # Superuser should be staff regardless of role
        super_user = UserFactory(is_superuser=True)
        assert super_user.is_staff is True
    
    def test_has_perm_method(self, db):
        """Test that has_perm method works correctly."""
        admin = AdminFactory(is_superuser=True)
        user = UserFactory()
        
        # Superusers should have all permissions
        assert admin.has_perm('any.permission') is True
        
        # Regular users don't have permissions by default
        assert user.has_perm('any.permission') is False
    
    def test_has_module_perms_method(self, db):
        """Test that has_module_perms method works correctly."""
        admin = AdminFactory(is_superuser=True)
        user = UserFactory()
        
        # Superusers should have all module permissions
        assert admin.has_module_perms('any_app') is True
        
        # Regular users don't have module permissions by default
        assert user.has_module_perms('any_app') is False


@pytest.mark.unit
class TestUserHelperMethods:
    """Test helper methods of the User model."""
    
    def test_get_full_name(self, db):
        """Test the get_full_name method."""
        user = UserFactory(username="full_name_test")
        assert user.get_full_name() == "full_name_test"
        
        # If username is not set, should return email
        user.username = ""
        assert user.get_full_name() == user.email
    
    def test_get_short_name(self, db):
        """Test the get_short_name method."""
        user = UserFactory(username="short_name_test")
        assert user.get_short_name() == "short_name_test"


@pytest.mark.unit
class TestUserFactories:
    """Test the user factories for specialized user types."""
    
    def test_admin_factory(self, db):
        """Test the AdminFactory creates users with admin role."""
        admin = AdminFactory()
        
        assert admin.role == Roles.AD
        assert admin.is_superuser is True
        assert admin.is_staff is True  # Via the property
        assert admin.email.startswith("admin")
    
    def test_moderator_factory(self, db):
        """Test the ModeratorFactory creates users with moderator role."""
        mod = ModeratorFactory()
        
        assert mod.role == Roles.MO
        assert mod.is_superuser is False
        assert mod.is_staff is False  # Moderators aren't staff by default
        assert mod.email.startswith("mod")
    
    def test_inactive_user_factory(self, db):
        """Test the InactiveUserFactory creates inactive users."""
        user = InactiveUserFactory()
        
        assert user.is_active is False
        assert user.role == Roles.US
    
    def test_new_user_factory(self, db):
        """Test the NewUserFactory creates recently created users."""
        user = NewUserFactory()
        
        # Should have recent timestamps
        now = timezone.now()
        delta = now - user.created_at
        assert delta < timedelta(minutes=10)  # Should be within 10 minutes
        assert delta > timedelta(minutes=1)   # But not too recent
    
    def test_user_with_activity_factory(self, db):
        """Test the UserWithActivityFactory creates users with login activity."""
        user = UserWithActivityFactory()
        
        # Should have last_login set
        assert user.last_login is not None
        
        # Should have login_count attribute
        assert hasattr(user, 'login_count')
        assert user.login_count == 5  # Default value
        
        # With custom login count
        user = UserWithActivityFactory(set_login_count=10)
        assert user.login_count == 10
    
    def test_create_users_with_different_roles(self, db):
        """Test the helper function creates users with different roles."""
        regular, admin, moderator = create_users_with_different_roles()
        
        assert regular.role == Roles.US
        assert admin.role == Roles.AD
        assert moderator.role == Roles.MO


@pytest.mark.unit
class TestModelPerformance:
    """Test performance-related aspects of the User model."""
    
    def test_indexes_exist(self, db):
        """Test that important indexes are defined."""
        # This test verifies the database has the defined indexes
        # Uses Django's introspection API
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check for email index
            cursor.execute(
                "SELECT 1 FROM pg_indexes WHERE tablename = 'user_management_user' AND indexname = 'user_management_user_email_f30049fa_idx'"
            )
            assert cursor.fetchone() is not None, "Email index not found"
            
            # Check for username index
            cursor.execute(
                "SELECT 1 FROM pg_indexes WHERE tablename = 'user_management_user' AND indexname = 'user_management_user_username_f4d2586a_idx'"
            )
            assert cursor.fetchone() is not None, "Username index not found"