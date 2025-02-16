from datetime import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from django.core.validators import MinLengthValidator
from django.db.models import UniqueConstraint, CheckConstraint, Q


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        epantherid = email.split('@')[0]
        user = self.model(email=email, epantherid=epantherid, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

class Roles(models.TextChoices):
    AD = "admin"
    US = "user"
    MO = "moderator"


class Sun_levels(models.TextChoices):
    FULLSUN = "full sun"
    PARTSUN = "partial sun"
    PARTSHADE = "partial shade"
    FULLSHADE = "full shade"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    user_password = models.CharField(_('password'), max_length=100, blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), blank=True, null=True, max_length=50)
    role = models.CharField(_('role'), max_length=9, choices=Roles.choices, default=Roles.US)
    is_active = models.BooleanField(_('active'), default=True) # not needed carryover
    zip_code = models.CharField(_('zip code'), blank=True, null=True, max_length=5, validators=[MinLengthValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        app_label = 'user_management'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f"{self.email} id:{self.id}"

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
    species = models.CharField(max_length=50)
    variety = models.CharField(blank=True, null=True, max_length=50)
    maturity_time = models.IntegerField() # in number of days
    is_deleted = models.BooleanField(default=False)
    # possible other attributes
    germination_time = models.IntegerField(blank=True, null=True) # in number of days
    spacing_x = models.IntegerField(blank=True, null=True) # in inches
    spacing_y = models.IntegerField(blank=True, null=True) # in inches
    sun_level = models.CharField(blank=True, null=True, max_length=13, choices=Sun_levels.choices)
    planting_depth = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2) # in inches
    water_req = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=2) # in inches
    plant_description = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            CheckConstraint(
                check = Q(maturity_time__gte=0), 
                name = 'check_maturity_pos',
            ),

            CheckConstraint(
                check = Q(germination_time__gte=0 or Q(germination_time__isnull=True)), 
                name = 'check_germ_pos',
            ),

            CheckConstraint(
                check = Q(spacing_x__gte=0 or Q(spacing_x__isnull=True)), 
                name = 'check_spacing_x_pos',
            ),

            CheckConstraint(
                check = Q(spacing_y__gte=0 or Q(spacing_y__isnull=True)), 
                name = 'check_spacing_y_pos',
            ),

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
    size_x = models.IntegerField() # in inches
    size_y = models.IntegerField() # in inches
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
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
        return f"user id:{self.user_id} - size:{self.size_x}x{self.size_y}"


class Garden_log(models.Model):
    garden_id = models.ForeignKey(Gardens, on_delete=models.CASCADE)
    plant_id = models.ForeignKey(Plants, on_delete=models.DO_NOTHING)
    # planted_date should be user entered rather than auto-generated/timestamp.
    planted_date = models.DateField()
    x_coordinate = models.IntegerField() # in inches
    y_coordinate = models.IntegerField() # in inches

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['garden_id', 'x_coordinate', 'y_coordinate'],
                name='unq_plot_space'
            ),

            CheckConstraint(
                check = Q(x_coordinate__gte=0), 
                name = 'check_x_coor_pos',
            ),

            CheckConstraint(
                check = Q(y_coordinate__gte=0), 
                name = 'check_y_coor_pos',
            ),
        ]
    
    def __str__(self):
        return f"garden:{self.garden_id} - plant:{self.plant_id} @ [{self.x_coordinate},{self.y_coordinate}]"
    

class Forums(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=50)
    body = models.TextField() # don't allow blank
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Forum ID:{self.id}"


class Replies(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    forum_id = models.ForeignKey(Forums, on_delete=models.DO_NOTHING)
    parent_id = models.ForeignKey("self", blank=True, null=True, on_delete=models.DO_NOTHING)
    # Note: if parent_id is null, its parent is the initial forum post indicated by forum_id
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Reply ID:{self.id}"
    

class Likes(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    reply_id = models.ForeignKey(Replies, on_delete=models.DO_NOTHING)
    ld_value = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user_id', 'reply_id'],
                name='unq_vote'
            )
        ]

    def __str__(self):
        return f"Like ID:{self.id}"

