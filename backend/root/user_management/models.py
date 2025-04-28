# backend/root/user_management/models.py
"""
User Models for UPlant Application

This module defines the core user authentication models that extend Django's
authentication system. It implements a custom User model using email as the 
primary identifier (rather than username) while maintaining compatibility with
Django's permission system.

Key components:
1. UserManager - Custom manager handling user creation with email-based lookups
2. Roles - Enum of user roles (Admin, User, Moderator)
3. User - Custom user model with role-based permissions

The User model supports:
- Email-based authentication
- Role-based permissions
- ZIP code for location-based features
- Tracking of creation/update timestamps
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    
    This manager extends Django's BaseUserManager to support email as the
    unique identifier for authentication instead of usernames. It provides
    methods for creating both regular users and superusers.
    
    Attributes:
        Inherits all attributes from BaseUserManager
    """
    
    def get_by_natural_key(self, email):
        """
        Retrieve a user by their natural key (email).
        
        Used by Django's authentication system to look up users.
        
        Args:
            email: The email address to search for
            
        Returns:
            User: User instance matching the email
            
        Raises:
            User.DoesNotExist: If no user with the email exists
        """
        return self.get(**{self.model.USERNAME_FIELD: email})

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        
        This is the core method used when registering new users.
        
        Args:
            email: User's email address (required)
            password: User's password (optional)
            **extra_fields: Additional fields to set on the user instance
            
        Returns:
            User: The newly created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError(_('The Email must be set'))
            
        # Normalize email to lowercase domain part
        email = self.normalize_email(email)
        
        # Create user instance but don't save it yet
        user = self.model(email=email, **extra_fields)
        
        # Handle password hashing using Django's security features
        user.set_password(password)
        
        # Save the user to the database
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        
        Superusers have all permissions by default.
        
        Args:
            email: Superuser's email address
            password: Superuser's password
            **extra_fields: Additional fields to set on the user instance
            
        Returns:
            User: The newly created superuser instance
            
        Raises:
            ValueError: If is_superuser is explicitly set to False
        """
        # Ensure superuser has is_superuser flag
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
            
        return self.create_user(email, password, **extra_fields)


class Roles(models.TextChoices):
    """
    Enumeration of user roles in the UPlant system.
    
    Defines the available roles and their internal/display values. Using Django's
    TextChoices provides type safety and clear display names for the admin interface.
    
    Attributes:
        AD: Admin role with highest level of permissions
        US: Regular user role (default for most users)
        MO: Moderator role with elevated permissions for content curation
    """
    AD = "Admin", "Admin"
    US = "User", "User"
    MO = "Moderator", "Moderator"


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for UPlant.
    
    This model extends Django's AbstractBaseUser and PermissionsMixin to create
    a fully-featured user model with:
    - Email-based authentication (instead of username-based)
    - Role-based permissions system
    - Location data through ZIP code
    - Creation and update timestamps
    
    By using AbstractBaseUser, we maintain compatibility with Django's auth system
    while customizing the fields and behaviors to meet UPlant's requirements.
    
    Attributes:
        email: User's email address (primary identifier for authentication)
        username: User's display name (unique but not used for authentication)
        role: User's role in the system (Admin, User, or Moderator)
        zip_code: 5-digit US ZIP code for location-based features
        created_at: Auto-populated timestamp of account creation
        updated_at: Auto-updated timestamp of last account modification
        is_active: Boolean indicating if account is active
    """
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), unique=True, max_length=50, default='default_username')
    role = models.CharField(_('role'), max_length=9, choices=Roles.choices, default=Roles.US)
    zip_code = models.CharField(
        _('zip code'),
        blank=True,
        null=True,
        max_length=5,
        validators=[MinLengthValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='last updated')
    is_active = models.BooleanField(default=True)

    # Link to the custom manager
    objects = UserManager()

    # Configure Django's auth system to use email as the username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Fields required when creating a superuser

    class Meta:
        """
        Metadata options for the User model.
        
        Configures model-level behaviors and database optimizations.
        """
        app_label = 'user_management'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            # Add database indexes for frequently queried fields
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        """
        String representation of the user.
        
        Returns:
            str: User's email and ID for easy identification
        """
        return f"{self.email} - ID:{self.id}"

    @classmethod
    def get_by_natural_key(cls, email):
        """
        Class method to retrieve a user by their natural key (email).
        
        This provides consistent behavior with the manager's method.
        
        Args:
            email: The email address to search for
            
        Returns:
            User: User instance matching the email
        """
        return cls.objects.get(**{cls.USERNAME_FIELD: email})
    
    def get_full_name(self):
        """
        Return the user's full identifier.
        
        Implements a method required by Django's User contract,
        falling back to email if username isn't set.
        
        Returns:
            str: Username or email
        """
        return self.username or self.email

    def get_short_name(self):
        """
        Return the user's short identifier.
        
        Implements a method required by Django's User contract.
        
        Returns:
            str: Username
        """
        return self.username

    @property
    def is_staff(self):
        """
        Determines if user has staff permissions.
        
        This property controls access to the Django admin site.
        Admin role users and superusers have staff access.
        
        Note: This is a property, not a field. Don't use in QuerySet filters.
        Use `role=Roles.AD OR is_superuser=True` instead.
        
        Returns:
            bool: True if user has staff/admin permissions
        """
        return self.role in [Roles.AD, Roles.MO] or self.is_superuser

    def has_perm(self, perm, obj=None):
        """
        Check if user has a specific permission.
        
        In this implementation, superusers have all permissions.
        More granular permission checks could be implemented here.
        
        Args:
            perm: The permission string to check
            obj: Optional object to check permissions against
            
        Returns:
            bool: True if user has permission
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Check if user has permissions to view the app with this app_label.
        
        In this implementation, superusers have access to all modules.
        
        Args:
            app_label: The application label to check permissions for
            
        Returns:
            bool: True if user has module permission
        """
        return self.is_superuser