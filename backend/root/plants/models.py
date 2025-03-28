# backend/root/plants/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, Q

# Debug statement
print("Loading plants.models module")

class Sun_levels(models.TextChoices):
    FULLSUN = "full sun"
    PARTSUN = "partial sun"
    PARTSHADE = "partial shade"
    FULLSHADE = "full shade"


class Plant(models.Model):
    species = models.CharField(_('species'), max_length=50)
    variety = models.CharField(_('variety'), blank=True, null=True, max_length=50)
    maturity_time = models.PositiveIntegerField(_('maturity time'))  # in number of days
    is_deleted = models.BooleanField(default=False)
    # possible other attributes
    germination_time = models.PositiveIntegerField(_('germination time'), blank=True, null=True)  # in number of days
    spacing_x = models.PositiveIntegerField(_('spacing length'), blank=True, null=True)  # in inches
    spacing_y = models.PositiveIntegerField(_('spacing width'), blank=True, null=True)  # in inches
    sun_level = models.CharField(_('sun level'), blank=True, null=True, max_length=13, choices=Sun_levels.choices)
    planting_depth = models.DecimalField(_('planting depth'), blank=True, null=True, max_digits=4, decimal_places=2)  # in inches
    water_req = models.DecimalField(_('water requirement'), blank=True, null=True, max_digits=4, decimal_places=2)  # in inches
    plant_description = models.TextField(_('plant description'), blank=True, null=True)

    class Meta:
        verbose_name = _('plant')
        verbose_name_plural = _('plants')
        
        constraints = [
            CheckConstraint(
                check=Q(planting_depth__gte=0) | Q(planting_depth__isnull=True),
                name='check_depth_pos',
            ),
            CheckConstraint(
                check=Q(water_req__gte=0) | Q(water_req__isnull=True),
                name='check_water_pos',
            ),
        ]
    
    def __str__(self):
        if self.variety:
            return f"{self.species} - {self.variety}"
        return self.species