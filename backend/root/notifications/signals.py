# backend/root/notifications/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from user_management.models import Notification, NotificationInstance
from django.utils import timezone
from datetime import timedelta
from gardens.models import GardenLog  # Assuming this links plants to gardens

@receiver(post_delete, sender=GardenLog)
def cleanup_orphaned_notifications(sender, instance, **kwargs):
    """When a plant is removed from a garden, check if notifications should be deleted"""
    garden = instance.garden
    plant = instance.plant
    
    # Check if this was the last instance of this plant in this garden
    if not GardenLog.objects.filter(garden=garden, plant=plant).exists():
        # Delete notifications that now have no associated plants
        Notification.objects.filter(garden=garden, plant=plant).delete()

@receiver(post_save, sender=Notification)
def create_notification_instance(sender, instance, created, **kwargs):
    """Create the first notification instance when a notification is created"""
    if created:
        # For new notifications, set up the first instance due today
        NotificationInstance.objects.create(
            notification=instance,
            next_due=timezone.now() + timedelta(days=instance.interval)
        )