# backend/root/notifications/models.py

from django.db import models
from django.db.models import CheckConstraint, Q
from plants.models import Plant
from gardens.models import GardenLog
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class NotifTypes(models.TextChoices):
    PR = "PR", "Prune"
    FE = "FE", "Fertilize"
    HA = "HA", "Harvest" 
    WA = "WA", "Water"
    WE = "WE", "Weather"
    OT = "OT", "Other"

class Notification(models.Model):
    garden = models.ForeignKey('gardens.Garden', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text="Name of the notification")
    type = models.CharField(max_length=9, choices=NotifTypes.choices)
    subtype = models.CharField(('notification subtype'), max_length=25, blank=True,
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
        if self.type != NotifTypes.OT and self.subtype:
            raise ValidationError({
                'subtype': _('Subtype should only be used with "Other" notification types')
            })
                
        # For "Other" notifications: require a subtype
        if self.type == NotifTypes.OT and not self.subtype:
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
    message = models.TextField(blank=True, null=True, help_text="Content of the notification")
    status = models.CharField(max_length=10, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
        ('MISSED', 'Missed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When the notification was completed")
    
    class Meta:
        ordering = ['next_due']  # Sort by due date by default
        indexes = [
            models.Index(fields=['next_due']),
            models.Index(fields=['status']),
        ]
    
    @property
    def is_overdue(self):
        if self.next_due is None:
            return False  # Not overdue if no due date set
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

    @classmethod
    def auto_process_old_notifications(cls, days_threshold=14):
        """
        Find very overdue notifications and automatically reschedule them.
        
        Args:
            days_threshold: Number of days after which a notification is considered missed
            
        Returns:
            dict: Statistics about processed notifications
        """
        threshold = timezone.now() - timedelta(days=days_threshold)
        
        # Find pending notifications that are significantly overdue
        overdue_instances = cls.objects.filter(
            next_due__lt=threshold,
            status='PENDING'
        )
        
        processed_count = 0
        for instance in overdue_instances:
            # Mark as missed and reschedule
            instance.status = 'MISSED'
            
            # Calculate next due date from current time (not from missed date)
            instance.next_due = timezone.now() + timedelta(days=instance.notification.interval)
            instance.save()
            
            # Create a new pending instance for the future
            cls.objects.create(
                notification=instance.notification,
                next_due=instance.next_due,
                status='PENDING'
            )
            
            processed_count += 1
        
        return {
            'processed': processed_count,
            'threshold_days': days_threshold,
            'timestamp': timezone.now()
        }

    def complete_task(self):
        """Record completion and calculate next due date"""
        self.last_completed = timezone.now()
        self.completed_at = timezone.now()
        
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