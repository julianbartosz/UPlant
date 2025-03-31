# backend/root/gardens/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.utils import timezone
from user_management.models import User
from plants.models import Plant

class Garden(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Owner of the garden")
    name = models.CharField(_('Garden Name'), max_length=25, null=True, blank=True)
    size_x = models.PositiveIntegerField(_('Garden Length'), help_text="Length of the garden (e.g., in inches)")
    size_y = models.PositiveIntegerField(_('Garden Width'), help_text="Width of the garden (e.g., in inches)")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the garden was created")
    is_deleted = models.BooleanField(default=False, help_text="Flag indicating if the garden is deleted (soft delete)")
    
    class Meta:
        verbose_name = _('garden')
        verbose_name_plural = _('gardens')
        constraints = [
            CheckConstraint(check=Q(size_x__gt=0), name='check_size_x_pos'),
            CheckConstraint(check=Q(size_y__gt=0), name='check_size_y_pos'),
        ]
    
    def __str__(self):
        return f"Garden {self.id} - {self.name or 'Unnamed'} ({self.size_x} x {self.size_y})"
    
    # Helper methods
    def total_plots(self):
        """Return the total number of plots in the garden grid."""
        return self.size_x * self.size_y
    
    def occupied_plots(self):
        """Return the number of occupied plots (i.e., logs associated with this garden)."""
        return self.gardenlog_set.count()
    
    def available_plots(self):
        """Return the number of available plots."""
        return self.total_plots() - self.occupied_plots()
    
    def is_plot_available(self, x, y):
        """
        Check if a specific plot (x, y) in the garden is available.
        Returns True if there is no GardenLog for the given coordinates.
        """
        return not self.gardenlog_set.filter(x_coordinate=x, y_coordinate=y).exists()


class GardenLog(models.Model):
    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, help_text="The garden to which this log belongs")
    plant = models.ForeignKey(
        'plants.Plant', on_delete=models.SET_NULL, null=True, blank=True, 
        help_text="The plant placed in the garden"
    ) # Consider CASCADE: When a Plant is deleted, all GardenLog records that reference that plant are automatically deleted as well.
    planted_date = models.DateField(_('Date Planted'), default=timezone.now, help_text="The date when the plant was planted")
    x_coordinate = models.PositiveIntegerField(_('X Coordinate'), help_text="X coordinate position in the garden grid")
    y_coordinate = models.PositiveIntegerField(_('Y Coordinate'), help_text="Y coordinate position in the garden grid")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when this log was last updated")
    
    class Meta:
        verbose_name = _('garden log')
        verbose_name_plural = _('garden logs')
        constraints = [
            UniqueConstraint(fields=['garden', 'x_coordinate', 'y_coordinate'], name='unique_plot_space')
        ]
        ordering = ['garden', 'planted_date']
    
    def __str__(self):
        plant_info = self.plant.scientific_name if self.plant else "Unknown Plant"
        return f"Garden {self.garden.id} - Plant: {plant_info} at [{self.x_coordinate}, {self.y_coordinate}]"
    
    def is_in_bounds(self):
        # Assumes coordinates start at 1 and must be <= garden dimensions.
        return self.x_coordinate <= self.garden.size_x and self.y_coordinate <= self.garden.size_y
