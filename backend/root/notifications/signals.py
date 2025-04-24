# backend/root/notifications/signals.py

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.cache import cache

from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation, NotifTypes
from gardens.models import GardenLog, Garden, PlantHealthStatus
from services.search_service import reindex_model

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
            
            # Find notifications for this specific plant in this garden
            plant_associations = NotificationPlantAssociation.objects.filter(
                plant=plant, 
                notification__garden=garden
            )
            
            # For each association, check if other plants exist in the notification
            for assoc in plant_associations:
                notification = assoc.notification
                plant_count = notification.plants.count()
                
                if plant_count <= 1:
                    # This is the only plant in the notification, delete the notification
                    notification.delete()
                    logger.info(f"Deleted notification {notification.id} after plant removal")
                else:
                    # Other plants exist, just remove this plant
                    notification.plants.remove(plant)
                    logger.info(f"Removed plant from notification {notification.id}")
                    
                # Clear cache either way
                clear_notification_cache(notification)
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
                # Check for watering events
                if instance.last_watered and old_log.last_watered != instance.last_watered:
                    mark_watering_completed(instance)
                
                # Check for fertilizing events
                if instance.last_fertilized and old_log.last_fertilized != instance.last_fertilized:
                    mark_fertilizing_completed(instance)
                
                # Check for pruning events
                if instance.last_pruned and old_log.last_pruned != instance.last_pruned:
                    mark_pruning_completed(instance)
                    
                # Check for health status changes
                if old_log.health_status != instance.health_status:
                    process_health_status_change(instance)
        except Exception as e:
            logger.error(f"Error processing garden log care activities: {e}")
    elif created and instance.plant:
        # For new plants, see if we need to create care notifications
        try:
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


def mark_watering_completed(garden_log):
    """Mark watering notifications as completed for a garden log"""
    garden = garden_log.garden
    plant = garden_log.plant
    
    if not plant:
        return
        
    # Find pending watering notifications for this plant in this garden
    instances = NotificationInstance.objects.filter(
        notification__garden=garden,
        notification__plants=plant,
        # Either "Water" type (if added) or "Other" with "Watering" subtype
        notification__type__in=['WA', 'OT'],
        notification__subtype__in=['Watering', ''],
        status='PENDING'
    )
    
    for instance in instances:
        # Mark as completed
        instance.status = 'COMPLETED'
        instance.last_completed = timezone.now()
        instance.save()
        logger.info(f"Marked watering notification {instance.id} as completed")


def mark_fertilizing_completed(garden_log):
    """Mark fertilizing notifications as completed for a garden log"""
    garden = garden_log.garden
    plant = garden_log.plant
    
    if not plant:
        return
        
    # Find pending fertilizing notifications for this plant in this garden
    instances = NotificationInstance.objects.filter(
        notification__garden=garden,
        notification__plants=plant,
        notification__type=NotifTypes.FE,
        status='PENDING'
    )
    
    for instance in instances:
        # Mark as completed
        instance.status = 'COMPLETED'
        instance.last_completed = timezone.now()
        instance.save()
        logger.info(f"Marked fertilizing notification {instance.id} as completed")


def mark_pruning_completed(garden_log):
    """Mark pruning notifications as completed for a garden log"""
    garden = garden_log.garden
    plant = garden_log.plant
    
    if not plant:
        return
        
    # Find pending pruning notifications for this plant in this garden
    instances = NotificationInstance.objects.filter(
        notification__garden=garden,
        notification__plants=plant,
        notification__type=NotifTypes.PR,
        status='PENDING'
    )
    
    for instance in instances:
        # Mark as completed
        instance.status = 'COMPLETED'
        instance.last_completed = timezone.now()
        instance.save()
        logger.info(f"Marked pruning notification {instance.id} as completed")


def process_health_status_change(garden_log):
    """Process plant health status changes and create alerts if needed"""
    if garden_log.health_status in [PlantHealthStatus.POOR, PlantHealthStatus.DYING]:
        logger.warning(f"Plant health declined to {garden_log.health_status} in garden {garden_log.garden.id}")
        
        # Create a health alert notification if one doesn't exist already
        garden = garden_log.garden
        plant = garden_log.plant
        
        if not plant:
            return
        
        # Check if we already have a health alert for this plant
        existing_alert = Notification.objects.filter(
            garden=garden,
            plants=plant,
            type=NotifTypes.OT,
            subtype='Health Alert'
        ).exists()
        
        if not existing_alert:
            # Create health alert notification
            notification = Notification.objects.create(
                garden=garden,
                name=f"{plant.common_name or 'Plant'} needs attention",
                type=NotifTypes.OT,
                subtype="Health Alert",
                interval=1  # One-time notification
            )
            notification.plants.add(plant)
            
            # Create immediate notification instance
            NotificationInstance.objects.create(
                notification=notification,
                next_due=timezone.now(),
                status='PENDING'
            )
            
            logger.info(f"Created health alert notification for plant {plant.id} in garden {garden.id}")


def create_plant_care_notifications(garden_log):
    """Create care notifications for a newly added plant based on its requirements"""
    plant = garden_log.plant
    garden = garden_log.garden
    
    if not plant:
        return
    
    # Get plant care requirements (if available)
    watering_frequency = getattr(plant, 'water_interval', 7)  # Default to weekly watering
    fertilizing_frequency = 30  # Default to monthly fertilizing
    pruning_frequency = 90      # Default to quarterly pruning
    
    # Create watering notification if frequency is available
    if watering_frequency and watering_frequency > 0:
        # Check if notification already exists
        if not Notification.objects.filter(
            garden=garden,
            plants=plant,
            type='OT',  # Or 'WA' if implemented
            subtype='Watering'
        ).exists():
            # Create watering notification
            notification = Notification.objects.create(
                garden=garden,
                name=f"Water {plant.common_name or 'plant'}",
                type='OT',  # Or 'WA' if implemented
                subtype='Watering',
                interval=watering_frequency
            )
            notification.plants.add(plant)
            logger.info(f"Created watering notification for plant {plant.id} in garden {garden.id}")
    
    # Create fertilizing notification if frequency is available
    if fertilizing_frequency and fertilizing_frequency > 0:
        # Check if notification already exists
        if not Notification.objects.filter(
            garden=garden,
            plants=plant,
            type=NotifTypes.FE
        ).exists():
            # Create fertilizing notification
            notification = Notification.objects.create(
                garden=garden,
                name=f"Fertilize {plant.common_name or 'plant'}",
                type=NotifTypes.FE,
                interval=fertilizing_frequency
            )
            notification.plants.add(plant)
            logger.info(f"Created fertilizing notification for plant {plant.id} in garden {garden.id}")
    
    # Create pruning notification if frequency is available  
    if pruning_frequency and pruning_frequency > 0:
        # Check if notification already exists
        if not Notification.objects.filter(
            garden=garden,
            plants=plant,
            type=NotifTypes.PR
        ).exists():
            # Create pruning notification
            notification = Notification.objects.create(
                garden=garden,
                name=f"Prune {plant.common_name or 'plant'}",
                type=NotifTypes.PR,
                interval=pruning_frequency
            )
            notification.plants.add(plant)
            logger.info(f"Created pruning notification for plant {plant.id} in garden {garden.id}")