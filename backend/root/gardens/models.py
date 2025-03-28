# backend/root/gardens/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, Q, UniqueConstraint
import datetime


class Gardens(models.Model):
    user_id = models.ForeignKey('user_management.User', on_delete=models.DO_NOTHING)
    name = models.CharField(_('garden name'), blank=True, null=True, max_length=25)
    size_x = models.PositiveIntegerField(_('garden length'))  # in inches
    size_y = models.PositiveIntegerField(_('garden width'))  # in inches
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('garden')
        verbose_name_plural = _('gardens')

        constraints = [
            CheckConstraint(
                check=Q(size_x__gt=0),
                name='check_size_x_pos',
            ),

            CheckConstraint(
                check=Q(size_y__gt=0),
                name='check_size_y_pos',
            ),
        ]
    
    def __str__(self):
        return f"garden id:{self.id} - size:{self.size_x}x{self.size_y}"


class Garden_log(models.Model):
    garden_id = models.ForeignKey(Gardens, on_delete=models.CASCADE)
    plant_id = models.ForeignKey('plants.Plant', on_delete=models.DO_NOTHING)
    planted_date = models.DateField(_('date planted'), default=datetime.date.today)  # note user-entered
    x_coordinate = models.PositiveIntegerField(_('x-coordinate location'))  # in inches
    y_coordinate = models.PositiveIntegerField(_('y-coordinate location'))  # in inches

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