# backend/root/user_management/tests/factories.py
import factory
import pytz
from datetime import datetime, timedelta
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory import fuzzy, Faker
from user_management.models import User, Roles

class BaseUserFactory(DjangoModelFactory):
    """
    Base factory for User model with common attributes.
    
    This abstract factory defines common attributes for all user types
    and shouldn't be used directly - use the concrete factories below.
    """
    class Meta:
        model = User
        abstract = True
        skip_postgeneration_save = True  # Added to fix deprecation warning

    # Use Faker for more realistic test data
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    zip_code = Faker('postcode')
    is_active = True
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    
    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        """
        Create profile-related data if needed.
        
        Args:
            create: Whether to create a new object or build an unsaved one
            extracted: Value passed in from factory call
            **kwargs: Additional attributes to set on the profile
        """
        if not create:
            return

        # If profile data is passed as a dict, set those attributes
        if extracted:
            for key, value in extracted.items():
                setattr(self, key, value)
            self.save()  # Explicitly save after setting attributes


class UserFactory(BaseUserFactory):
    """
    Factory for regular users with default settings.
    
    Examples:
        # Create basic user
        user = UserFactory()
        
        # Create user with specific attributes
        user = UserFactory(email='specific@example.com', username='specificuser')
        
        # Create inactive user
        user = UserFactory(is_active=False)
    """
    class Meta:
        model = User
        skip_postgeneration_save = True  # Added to fix deprecation warning
        
    role = Roles.US


class AdminFactory(BaseUserFactory):
    """
    Factory for admin users with appropriate permissions.
    
    Examples:
        # Create basic admin
        admin = AdminFactory()
        
        # Create admin with specific attributes
        admin = AdminFactory(email='admin@example.com')
    """
    class Meta:
        model = User
        skip_postgeneration_save = True  # Added to fix deprecation warning
        
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    username = factory.Sequence(lambda n: f'admin{n}')
    role = Roles.AD
    is_superuser = True


class ModeratorFactory(BaseUserFactory):
    """
    Factory for moderator users.
    
    Examples:
        # Create basic moderator
        mod = ModeratorFactory()
    """
    class Meta:
        model = User
        skip_postgeneration_save = True  # Added to fix deprecation warning
        
    email = factory.Sequence(lambda n: f'mod{n}@example.com')
    username = factory.Sequence(lambda n: f'mod{n}')
    role = Roles.MO


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive users for testing account activation flows."""
    class Meta:
        model = User
        skip_postgeneration_save = True  # Added to fix deprecation warning
        
    is_active = False


class NewUserFactory(UserFactory):
    """
    Factory for newly created users (recent timestamps).
    
    Useful for testing new user flows and welcome emails.
    """
    class Meta:
        model = User
        skip_postgeneration_save = True  # Added to fix deprecation warning
        
    created_at = factory.LazyFunction(lambda: timezone.now() - timedelta(minutes=5))
    updated_at = factory.LazyFunction(lambda: timezone.now() - timedelta(minutes=5))


class UserWithActivityFactory(UserFactory):
    """
    Factory for users with login activity.
    
    Useful for testing user activity reports and dashboards.
    """
    class Meta:
        model = User
        skip_postgeneration_save = True  # Added to fix deprecation warning
        
    last_login = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=2))

    @factory.post_generation
    def set_login_count(self, create, extracted, **kwargs):
        """Set login count if specified."""
        if not create:
            return
        
        # Set a login count attribute for testing (not a real model field)
        self.login_count = extracted or 5
        self.save()  # Explicitly save after setting login_count


# Factory build helpers
def create_users_with_different_roles():
    """
    Create one user of each role type.
    
    Returns:
        tuple: (regular_user, admin_user, moderator_user)
    """
    regular_user = UserFactory()
    admin_user = AdminFactory()
    moderator_user = ModeratorFactory()
    return regular_user, admin_user, moderator_user