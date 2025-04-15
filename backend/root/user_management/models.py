# backend/root/user_management/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from django.db.models import CheckConstraint, Q
from plants.models import Plant
from gardens.models import GardenLog
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

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
        return self.role in [Roles.AD] or self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


    
class NotifTypes(models.TextChoices):
    PR = "Prune"
    FE = "Fertilize"
    HA = "Harvest"
    OT = "Other"

class Notification(models.Model):
    garden = models.ForeignKey('gardens.Garden', on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    type = models.CharField(max_length=9, choices=NotifTypes.choices)
    subtype = models.CharField(_('notification subtype'), max_length=25, blank=True,
                            help_text="Additional categorization for custom notifications")
    interval = models.PositiveIntegerField()
    # Instead of a direct plant FK, many-to-many:
    plants = models.ManyToManyField(Plant, through='NotificationPlantAssociation')
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when this notification was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when this notification was last updated")
    
    class Meta:
        constraints = [
            CheckConstraint(check=Q(interval__gt=0), name='check_interval')
        ]
    
    def __str__(self):
        return f"Notification: {self.id} - {self.name}"
    
    def clean(self):
        # For standard notification types, subtype must be blank
        if self.type != 'OT' and self.subtype:
            raise ValidationError({
                'subtype': _('Subtype should only be used with "Other" notification types')
            })
            
        # For standard notifications: Check uniqueness without subtype
        if self.type != 'OT':
            if Notification.objects.filter(
                garden=self.garden, 
                plant=self.plant,
                type=self.type
            ).exclude(pk=self.pk).exists():
                raise ValidationError({
                    'type': _('This plant already has a notification of this type in this garden')
                })
                
        # For "Other" notifications: require a subtype
        if self.type == 'OT' and not self.subtype:
            raise ValidationError({
                'subtype': _('Subtype is required for "Other" notification types')
            })
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class NotificationPlantAssociation(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    custom_interval = models.PositiveIntegerField(null=True, blank=True)  # Override default interval
    
    class Meta:
        unique_together = ('notification', 'plant')

    def clean(self):
        if NotificationPlantAssociation.objects.filter(
            plant=self.plant,
            notification__type=self.notification.type,
            notification__garden=self.notification.garden
        ).exclude(id=self.id).exists():
            raise ValidationError(
                "This plant already has a notification of this type in this garden"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class NotificationInstance(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='instances')
    last_completed = models.DateTimeField(null=True, blank=True)
    next_due = models.DateTimeField()
    
    # Add metadata and additional fields
    status = models.CharField(max_length=10, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_due']  # Sort by due date by default
        indexes = [
            models.Index(fields=['next_due']),
            models.Index(fields=['status']),
        ]
    
    @property
    def is_overdue(self):
        return timezone.now() > self.next_due
    
    def is_harvest_ready(self):
        """Check if plants associated with this notification are ready for harvest"""
        # Only apply to harvest notifications
        if self.notification.type != NotifTypes.HA:
            return True  # Non-harvest notifications don't need this check
            
        ready_plants = []
        for assoc in NotificationPlantAssociation.objects.filter(notification=self.notification):
            plant = assoc.plant
            
            # Check if plant has days_to_harvest data
            if not plant.days_to_harvest:
                continue
                
            garden_logs = GardenLog.objects.filter(
                garden=self.notification.garden, 
                plant=plant
            )
            
            for log in garden_logs:
                if log.planted_date:
                    days_grown = (timezone.now().date() - log.planted_date).days
                    if days_grown >= plant.days_to_harvest:
                        ready_plants.append(plant)
                        break
        
        # Return True if at least one plant is ready for harvest
        return len(ready_plants) > 0

    @classmethod
    def get_active_notifications(cls):
        """Get notification instances that are active and relevant"""
        base_queryset = cls.objects.filter(status='PENDING')
        
        # Manually filter out harvest notifications for plants that aren't ready
        result = []
        for instance in base_queryset:
            if instance.notification.type == NotifTypes.HA and not instance.is_harvest_ready():
                continue  # Skip harvest notifications for plants that aren't ready
            result.append(instance)
            
        return result
    
    def complete_task(self):
        """Record completion and calculate next due date"""
        self.last_completed = timezone.now()
        
        # For harvest notifications, only schedule next one if plant will be ready again
        if self.notification.type == NotifTypes.HA:
            # For now, use normal interval, but we could calculate a specific next harvest date based on growing season
            self.next_due = self.last_completed + timedelta(days=self.notification.interval)
            # Might want to hide this notification until next growing season
        else:
            # Normal interval for other notification types
            self.next_due = self.last_completed + timedelta(days=self.notification.interval)
            
        self.status = 'COMPLETED'
        self.save()
        
    def skip_task(self):
        """Skip this instance and calculate next due date"""
        self.status = 'SKIPPED'
        self.next_due = timezone.now() + timedelta(days=self.notification.interval)
        self.save()
    
    def __str__(self):
        return f"{self.notification.name} - Due: {self.next_due.strftime('%Y-%m-%d')}"