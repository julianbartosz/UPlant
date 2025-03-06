from datetime import timezone
import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from django.core.validators import MinLengthValidator
from django.db.models import UniqueConstraint, CheckConstraint, Q


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
    AD = "Admin"
    US = "User"
    MO = "Moderator"


class Sun_levels(models.TextChoices):
    FULLSUN = "full sun"
    PARTSUN = "partial sun"
    PARTSHADE = "partial shade"
    FULLSHADE = "full shade"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), unique=True, max_length=50)
    role = models.CharField(_('role'), max_length=9, choices=Roles.choices, default=Roles.US)
    zip_code = models.CharField(_('zip code'), blank=True, null=True, max_length=5, validators=[MinLengthValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        app_label = 'user_management'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f"{self.email} id:{self.id}"

    @classmethod
    def get_by_natural_key(cls, username):
        return cls.objects.get(**{cls.USERNAME_FIELD: username})
    
    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self):
        return self.first_name

    @property
    def is_staff(self):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Plants(models.Model):
    species = models.CharField(_('species'), max_length=50)
    variety = models.CharField(_('variety'), blank=True, null=True, max_length=50)
    maturity_time = models.PositiveIntegerField(_('maturity time')) # in number of days
    is_deleted = models.BooleanField(default=False)
    # possible other attributes
    germination_time = models.PositiveIntegerField(_('germination time'), blank=True, null=True) # in number of days
    spacing_x = models.PositiveIntegerField(_('spacing length'), blank=True, null=True) # in inches
    spacing_y = models.PositiveIntegerField(_('spacing width'), blank=True, null=True) # in inches
    sun_level = models.CharField(_('sun level'), blank=True, null=True, max_length=13, choices=Sun_levels.choices)
    planting_depth = models.DecimalField(_('planting depth'), blank=True, null=True, max_digits=4, decimal_places=2) # in inches
    water_req = models.DecimalField(_('water requirement'), blank=True, null=True, max_digits=4, decimal_places=2) # in inches
    plant_description = models.TextField(_('plant description'), blank=True, null=True)

    class Meta:
        verbose_name = _('plant')
        verbose_name_plural = _('plants')

        constraints = [
            CheckConstraint(
                check = Q(planting_depth__gte=0 or Q(planting_depth__isnull=True)), 
                name = 'check_depth_pos',
            ),

            CheckConstraint(
                check = Q(water_req__gte=0 or Q(water_req__isnull=True)), 
                name = 'check_water_pos',
            ),
        ]
    
    def __str__(self):
        return f"{self.species} - {self.variety}"


class Gardens(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    name = models.CharField(_('garden name'), blank=True, null=True, max_length=25)
    size_x = models.PositiveIntegerField(_('garden length')) # in inches
    size_y = models.PositiveIntegerField(_('garden width')) # in inches
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('garden')
        verbose_name_plural = _('gardens')

        constraints = [
            CheckConstraint(
                check = Q(size_x__gt=0), 
                name = 'check_size_x_pos',
            ),

            CheckConstraint(
                check = Q(size_y__gt=0), 
                name = 'check_size_y_pos',
            ),
        ]
    
    def __str__(self):
        return f"garden id:{self.id} - size:{self.size_x}x{self.size_y}"


class Garden_log(models.Model):
    garden_id = models.ForeignKey(Gardens, on_delete=models.CASCADE)
    plant_id = models.ForeignKey(Plants, on_delete=models.DO_NOTHING)
    planted_date = models.DateField(_('date planted'), default=datetime.date.today) # note user-entered
    x_coordinate = models.PositiveIntegerField(_('x-coordinate location')) # in inches
    y_coordinate = models.PositiveIntegerField(_('y-coordinate location')) # in inches

    class Meta:
        verbose_name = _('garden log')
        verbose_name_plural = _('garden logs')

        constraints = [
            UniqueConstraint(
                fields=['garden_id', 'x_coordinate', 'y_coordinate'],
                name='unq_plot_space'
            )
        ]
    
    def __str__(self):
        return f"garden:{self.garden_id.id} - plant:({self.plant_id}) @ [{self.x_coordinate},{self.y_coordinate}]"
    
    def is_in_bounds(self):
        record = Gardens.objects.get(pk=self.garden_id.id)
        if record.size_x < self.x_coordinate or record.size_y < self.y_coordinate:
            return False
        else:
            return True
    

class Forums(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    title = models.CharField(_('title'), max_length=50)
    body = models.TextField(_('body')) # don't allow blank
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('forum')
        verbose_name_plural = _('forums')

    def __str__(self):
        return f"Forum ID:{self.id}"


class Replies(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    forum_id = models.ForeignKey(Forums, on_delete=models.CASCADE)
    parent_id = models.ForeignKey("self", blank=True, null=True, on_delete=models.DO_NOTHING)
    # Note: if parent_id is null, its parent is the initial forum post indicated by forum_id
    body = models.TextField(_('body'))
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('reply')
        verbose_name_plural = _('replies')

    def __str__(self):
        return f"Reply ID:{self.id}"

    ld_value = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        constraints = [
            UniqueConstraint(
                fields=['user_id', 'reply_id'],
                name='unq_vote'
            )
        ]

    def __str__(self):
        return f"Like ID:{self.id}"
