# backend/root/user_management/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(**{self.model.USERNAME_FIELD: email})

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class Roles(models.TextChoices):
    AD = "Admin", "Admin"
    US = "User", "User"
    MO = "Moderator", "Moderator"

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), unique=True, max_length=50, default='default_username')
    role = models.CharField(_('role'), max_length=9, choices=Roles.choices, default=Roles.US)
    zip_code = models.CharField(_('zip code'), blank=True, null=True, max_length=5, validators=[MinLengthValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='last updated')
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        app_label = 'user_management'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"{self.email} - ID:{self.id}"

    @classmethod
    def get_by_natural_key(cls, email):
        return cls.objects.get(**{cls.USERNAME_FIELD: email})
    
    def get_full_name(self):
        return self.username or self.email

    def get_short_name(self):
        return self.username

    @property
    def is_staff(self):
        return self.role in [Roles.AD]

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
