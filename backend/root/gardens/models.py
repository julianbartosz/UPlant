# backend/root/gardens/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.utils import timezone
from user_management.models import User
from plants.models import Plant

class Garden(models.Model):
    """
    The Garden model represents a user's virtual garden space with dimensions.
    Each garden belongs to a user and can contain multiple plants (GardenLogs).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                           help_text="Owner of the garden",
                           related_name="gardens")
    name = models.CharField(_('Garden Name'), max_length=50, null=True, blank=True)
    description = models.TextField(_('Description'), blank=True, null=True,
                                 help_text="Description or notes about this garden")
    size_x = models.PositiveIntegerField(_('Garden Length'), 
                                       help_text="Length of the garden (e.g., in inches)")
    size_y = models.PositiveIntegerField(_('Garden Width'), 
                                       help_text="Width of the garden (e.g., in inches)")
    created_at = models.DateTimeField(auto_now_add=True, 
                                    help_text="Timestamp when the garden was created")
    updated_at = models.DateTimeField(auto_now=True,
                                    help_text="Timestamp when the garden was last updated")
    is_deleted = models.BooleanField(default=False, 
                                   help_text="Flag for soft deletion")
    is_public = models.BooleanField(default=False,
                                  help_text="Whether this garden is visible to other users")
    location = models.CharField(max_length=100, blank=True, null=True,
                              help_text="General location of the garden (e.g., 'Backyard', 'Balcony')")
    # could be used for garden categorization
    garden_type = models.CharField(max_length=50, blank=True, null=True,
                                 help_text="Type of garden (e.g., 'Vegetable', 'Herb', 'Flower')")
    
    class Meta:
        verbose_name = _('garden')
        verbose_name_plural = _('gardens')
        ordering = ['-updated_at']
        constraints = [
            CheckConstraint(check=Q(size_x__gt=0), name='check_size_x_coordinate'),
            CheckConstraint(check=Q(size_y__gt=0), name='check_size_y_coordinate'),
        ]
    
    def __str__(self):
        return f"Garden {self.id} - {self.name or 'Unnamed'} ({self.size_x} x {self.size_y})"
    
    # Helper methods
    def total_plots(self):
        """Return the total number of plots in the garden grid."""
        return self.size_x * self.size_y
    
    def occupied_plots(self):
        """Return the number of occupied plots (i.e., logs associated with this garden)."""
        return self.logs.count()
    
    def available_plots(self):
        """Return the number of available plots."""
        return self.total_plots() - self.occupied_plots()
    
    def is_plot_available(self, x, y):
        """
        Check if a specific plot (x, y) in the garden is available.
        Returns True if there is no GardenLog for the given coordinates.
        """
        return not self.logs.filter(x_coordinate=x, y_coordinate=y).exists()

    def get_plant_counts(self):
        """Return a dictionary of plant counts by plant type."""
        return self.logs.values('plant__common_name').annotate(count=models.Count('id'))
    
    def get_recent_activity(self, days=30):
        """Return garden logs with activity in the last X days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.logs.filter(
            models.Q(planted_date__gte=cutoff_date) | 
            models.Q(updated_at__gte=cutoff_date)
        )


class PlantHealthStatus(models.TextChoices):
    """Plant health status choices for garden logs"""
    EXCELLENT = "Excellent", _("Excellent")
    HEALTHY = "Healthy", _("Healthy")
    FAIR = "Fair", _("Fair")
    POOR = "Poor", _("Poor")
    DYING = "Dying", _("Dying")
    DEAD = "Dead", _("Dead")
    UNKNOWN = "Unknown", _("Unknown")


class GardenLog(models.Model):
    """
    The GardenLog model represents a plant placed in a garden.
    It tracks position, health status, planting date, and care history.
    """
    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, 
                             help_text="The garden to which this log belongs",
                             related_name="logs")
    plant = models.ForeignKey('plants.Plant', on_delete=models.SET_NULL, null=True, blank=True, 
                            help_text="The plant placed in the garden")
    planted_date = models.DateField(_('Date Planted'), default=timezone.now, 
                                  help_text="The date when the plant was planted")
    x_coordinate = models.PositiveIntegerField(_('X Coordinate'), 
                                          help_text="X coordinate in the garden grid (0-based)")
    y_coordinate = models.PositiveIntegerField(_('Y Coordinate'), 
                                          help_text="Y coordinate in the garden grid (0-based)")
    health_status = models.CharField(_('Health Status'), max_length=15,
                                   choices=PlantHealthStatus.choices,
                                   default=PlantHealthStatus.HEALTHY,
                                   help_text="Current health status of the plant")
    notes = models.TextField(_('Notes'), blank=True, null=True,
                           help_text="Additional notes about this plant in the garden")
    last_watered = models.DateTimeField(null=True, blank=True,
                                      help_text="When the plant was last watered")
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when this log was created"
    )
    updated_at = models.DateTimeField(auto_now=True, 
                                    help_text="Timestamp when this log was last updated")
    
    # care tracking fields
    last_fertilized = models.DateTimeField(null=True, blank=True,
                                         help_text="When the plant was last fertilized")
    last_pruned = models.DateTimeField(null=True, blank=True,
                                     help_text="When the plant was last pruned")
    growth_stage = models.CharField(max_length=50, blank=True, null=True,
                                  help_text="Current growth stage of the plant")
    
    class Meta:
        verbose_name = _('garden log')
        verbose_name_plural = _('garden logs')
        unique_together = ('garden', 'x_coordinate', 'y_coordinate')
        ordering = ['garden', 'planted_date']
    
    def __str__(self):
        plant_info = self.plant.common_name if self.plant and self.plant.common_name else (
            self.plant.scientific_name if self.plant else "Unknown Plant"
        )
        return f"Garden {self.garden.id} - Plant: {plant_info} at [{self.x_coordinate}, {self.y_coordinate}]"
    
    def is_in_bounds(self):
        """Check if the garden log's position is within the garden's boundaries."""
        return (0 <= self.x_coordinate < self.garden.size_x and 
                0 <= self.y_coordinate < self.garden.size_y)

    def record_watering(self):
        """Record that this plant has been watered."""
        self.last_watered = timezone.now()
        self.save(update_fields=['last_watered', 'updated_at'])

    def record_fertilizing(self):
        """Record that this plant has been fertilized."""
        self.last_fertilized = timezone.now()
        self.save(update_fields=['last_fertilized', 'updated_at'])
    
    def record_pruning(self):
        """Record that this plant has been pruned."""
        self.last_pruned = timezone.now()
        self.save(update_fields=['last_pruned', 'updated_at'])
    
    def days_since_watered(self):
        """Return the number of days since this plant was last watered."""
        if not self.last_watered:
            return None
        return (timezone.now() - self.last_watered).days
    
    def days_since_planted(self):
        """Return the number of days since this plant was planted."""
        return (timezone.now().date() - self.planted_date).days