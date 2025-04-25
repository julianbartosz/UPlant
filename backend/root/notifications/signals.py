# backend/root/notifications/signals.py

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation
from gardens.models import GardenLog

logger = logging.getLogger(__name__)

# ==================== NOTIFICATION SIGNALS ====================

@receiver(post_save, sender=Notification)
def notification_saved_handler(sender, instance, created, **kwargs):
    """Handle notification creation and updates"""
    if created:
        # Create the first notification instance for a new notification
        logger.info(f"Creating first instance for notification {instance.id}: {instance.name}")
        
        # Skip during fixtures loading
        if kwargs.get('raw', False):
            return
            
        try:
            create_first_notification_instance(instance)
        except Exception as e:
            logger.error(f"Error creating first notification instance: {e}")
    
    # Clear cache on update as well
    clear_notification_cache(instance)


@receiver(post_delete, sender=Notification)
def notification_deleted_handler(sender, instance, **kwargs):
    """Clean up when a notification is deleted"""
    logger.info(f"Notification deleted: {instance.id} - {instance.name}")
    clear_notification_cache(instance)


# ==================== NOTIFICATION INSTANCE SIGNALS ====================

@receiver(post_save, sender=NotificationInstance)
def instance_saved_handler(sender, instance, created, **kwargs):
    """Handle notification instance updates"""
    if not created:
        # Check if status changed to COMPLETED or SKIPPED
        try:
            # Skip during fixtures loading
            if kwargs.get('raw', False):
                return
                
            old_instance = getattr(instance, '_prev_instance', None)
            if old_instance and old_instance.status != instance.status:
                if instance.status == 'COMPLETED':
                    # Schedule next instance if this was completed
                    schedule_next_notification(instance)
                elif instance.status == 'SKIPPED':
                    # Schedule next instance if this was skipped
                    schedule_next_notification(instance)
        except Exception as e:
            logger.error(f"Error processing notification instance status change: {e}")
    
    clear_notification_cache(instance.notification)


@receiver(pre_save, sender=NotificationInstance)
def instance_before_save(sender, instance, **kwargs):
    """Store previous instance state to detect changes"""
    if instance.pk:
        try:
            instance._prev_instance = NotificationInstance.objects.get(pk=instance.pk)
        except NotificationInstance.DoesNotExist:
            pass


# ==================== GARDEN LOG SIGNALS ====================

@receiver(post_delete, sender=GardenLog)
def cleanup_orphaned_notifications(sender, instance, **kwargs):
    """When a plant is removed from a garden, check if notifications should be deleted"""
    garden = instance.garden
    plant = instance.plant
    
    if not plant:
        return
    
    try:
        # Check if this was the last instance of this plant in this garden
        if not GardenLog.objects.filter(garden=garden, plant=plant).exists():
            logger.info(f"No more {plant} in garden {garden.id}, cleaning up notifications")
            
            # Lazy import to avoid circular import
            from services.notification_service import cleanup_plant_notifications
            cleanup_plant_notifications(garden, plant)
            
    except Exception as e:
        logger.error(f"Error cleaning up notifications after plant removal: {e}")


@receiver(post_save, sender=GardenLog)
def process_garden_log_care_activities(sender, instance, created, **kwargs):
    """Process garden log care activities and update related notifications"""
    # Skip during fixtures loading
    if kwargs.get('raw', False):
        return
        
    # If this is a care activity update, mark related notifications as completed
    if not created:
        try:
            old_log = getattr(instance, '_prev_log', None)
            if old_log:
                # Lazy import
                from services.notification_service import handle_plant_care_event, handle_health_change
                
                # Check for watering events
                if instance.last_watered and old_log.last_watered != instance.last_watered:
                    handle_plant_care_event(instance, 'watering')
                
                # Check for fertilizing events
                if instance.last_fertilized and old_log.last_fertilized != instance.last_fertilized:
                    handle_plant_care_event(instance, 'fertilizing')
                
                # Check for pruning events
                if instance.last_pruned and old_log.last_pruned != instance.last_pruned:
                    handle_plant_care_event(instance, 'pruning')
                    
                # Check for health status changes
                if old_log.health_status != instance.health_status:
                    handle_health_change(old_log.health_status, instance.health_status, 
                                        instance.garden, instance.plant)
        except Exception as e:
            logger.error(f"Error processing garden log care activities: {e}")
    elif created and instance.plant:
        # For new plants, see if we need to create care notifications
        try:
            # Lazy import
            from services.notification_service import create_plant_care_notifications
            create_plant_care_notifications(instance)
        except Exception as e:
            logger.error(f"Error creating plant care notifications: {e}")


@receiver(pre_save, sender=GardenLog)
def garden_log_before_save(sender, instance, **kwargs):
    """Store previous log state to detect changes"""
    if instance.pk:
        try:
            instance._prev_log = GardenLog.objects.get(pk=instance.pk)
        except GardenLog.DoesNotExist:
            pass


# ==================== PLANT ASSOCIATION SIGNALS ====================

@receiver(post_save, sender=NotificationPlantAssociation)
def plant_associated_handler(sender, instance, created, **kwargs):
    """Handle when a plant is associated with a notification"""
    if created and not kwargs.get('raw', False):
        logger.info(f"Plant {instance.plant_id} added to notification {instance.notification_id}")
        clear_notification_cache(instance.notification)


@receiver(post_delete, sender=NotificationPlantAssociation)
def plant_disassociated_handler(sender, instance, **kwargs):
    """Handle when a plant is removed from a notification"""
    logger.info(f"Plant {instance.plant_id} removed from notification {instance.notification_id}")
    
    # If this was the last plant, delete the notification
    try:
        notification = instance.notification
        if notification.notificationplantassociation_set.count() == 0:
            logger.info(f"No more plants in notification {notification.id}, deleting it")
            notification.delete()
        
        clear_notification_cache(notification)
    except Exception as e:
        logger.error(f"Error handling plant disassociation: {e}")


# ==================== HELPER FUNCTIONS ====================

def create_first_notification_instance(notification):
    """Create the first notification instance for a new notification"""
    # Use now + interval for first due date
    next_due = timezone.now() + timedelta(days=notification.interval)
    
    NotificationInstance.objects.create(
        notification=notification,
        next_due=next_due,
        status='PENDING'
    )
    
    logger.info(f"Created notification instance for {notification.name}, due {next_due}")


def schedule_next_notification(instance):
    """Schedule the next notification instance after completing or skipping one"""
    notification = instance.notification
    
    # Don't create new instances for one-time notifications (interval <= 0)
    if notification.interval <= 0:
        logger.info(f"Not scheduling next instance for one-time notification {notification.id}")
        return
    
    # Calculate next due date based on the current one
    if instance.status == 'COMPLETED':
        # For completed tasks, count from completion time
        next_due = timezone.now() + timedelta(days=notification.interval)
        logger.info(f"Creating next instance for completed notification {notification.id}, due {next_due}")
    else:
        # For skipped tasks, count from when it was due
        next_due = instance.next_due + timedelta(days=notification.interval)
        logger.info(f"Creating next instance for skipped notification {notification.id}, due {next_due}")
    
    # Create the next instance
    NotificationInstance.objects.create(
        notification=notification,
        next_due=next_due,
        status='PENDING'
    )


def clear_notification_cache(notification):
    """Clear cache entries related to notifications"""
    # Only attempt if notification has ID and garden
    if not notification or not notification.id or not hasattr(notification, 'garden'):
        return
        
    try:
        garden = notification.garden
        user = garden.user
        
        # Clear notification-specific cache
        cache.delete(f"notification:{notification.id}")
        
        # Clear garden notification lists
        cache.delete(f"garden:{garden.id}:notifications")
        
        # Clear user's notification dashboard
        cache.delete(f"user:{user.id}:notification_dashboard")
        cache.delete(f"user:{user.id}:upcoming_notifications")
        
        # Clear garden dashboard which includes notifications
        cache.delete(f"user:{user.id}:garden_dashboard")
    except Exception as e:
        logger.error(f"Error clearing notification cache: {e}")