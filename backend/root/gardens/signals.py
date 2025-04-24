# backend/root/gardens/signals.py

import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.conf import settings

from gardens.models import Garden, GardenLog, PlantHealthStatus
from notifications.models import Notification, NotificationInstance, NotifTypes
from services.search_service import reindex_model

logger = logging.getLogger(__name__)

# ==================== GARDEN SIGNALS ====================

@receiver(post_save, sender=Garden)
def garden_saved_handler(sender, instance, created, **kwargs):
    """Handle garden creation and updates"""
    if created:
        # Garden was just created
        logger.info(f"New garden created: {instance.name or 'Unnamed'} (ID: {instance.id})")
        
        # Initialize welcome notification for new gardens
        if not kwargs.get('raw', False):  # Skip during fixtures loading
            try:
                create_welcome_notification(instance)
            except Exception as e:
                logger.error(f"Failed to create welcome notification: {e}")
    else:
        # Garden was updated
        logger.debug(f"Garden updated: {instance.name or 'Unnamed'} (ID: {instance.id})")
        
        # Clear garden cache
        clear_garden_cache(instance)
    
    # Update search index
    if hasattr(settings, 'ENABLE_SEARCH_INDEXING') and settings.ENABLE_SEARCH_INDEXING:
        transaction.on_commit(lambda: reindex_model(Garden, [instance.id]))


@receiver(pre_save, sender=Garden)
def garden_before_save(sender, instance, **kwargs):
    """Process garden before saving"""
    if instance.pk:
        # This is an update, not a creation
        try:
            old_garden = Garden.objects.get(pk=instance.pk)
            
            # Check if garden dimensions changed
            if (old_garden.size_x != instance.size_x or 
                old_garden.size_y != instance.size_y):
                logger.info(f"Garden {instance.id} dimensions changed from "
                           f"({old_garden.size_x}x{old_garden.size_y}) to "
                           f"({instance.size_x}x{instance.size_y})")
                
                out_of_bounds = GardenLog.objects.filter(
                    Q(x_coordinate__gte=instance.size_x) |
                    Q(y_coordinate__gte=instance.size_y),
                    garden=instance
                ).count()
                
                if out_of_bounds > 0:
                    logger.warning(
                        f"Garden resize will place {out_of_bounds} plants outside boundaries"
                    )
        except Garden.DoesNotExist:
            # New garden, nothing to do
            pass


# ==================== GARDEN LOG SIGNALS ====================

@receiver(post_save, sender=GardenLog)
def garden_log_saved_handler(sender, instance, created, **kwargs):
    """Handle garden log creation and updates"""
    garden = instance.garden
    plant = instance.plant
    
    if created:
        # New plant added to garden
        logger.info(f"Plant {plant.common_name or plant.scientific_name or 'Unknown'} "
                   f"added to garden {garden.name or 'Unnamed'} at position "
                   f"({instance.x_coordinate}, {instance.y_coordinate})")
        
        # Create care notifications for this plant if plant has care requirements
        if not kwargs.get('raw', False):  # Skip during fixtures loading
            try:
                create_plant_care_notifications(instance)
            except Exception as e:
                logger.error(f"Failed to create plant care notifications: {e}")
    else:
        # Plant log updated
        try:
            old_log = GardenLog.objects.get(pk=instance.pk)
            
            # Check if health status changed
            if old_log.health_status != instance.health_status:
                process_health_status_change(old_log, instance)
                
            # Check if plant was moved
            if (old_log.x_coordinate != instance.x_coordinate or 
                old_log.y_coordinate != instance.y_coordinate):
                logger.info(f"Plant moved from ({old_log.x_coordinate}, {old_log.y_coordinate}) to "
                           f"({instance.x_coordinate}, {instance.y_coordinate}) in garden {garden.id}")
            
            # Check if care activities were performed
            if old_log.last_watered != instance.last_watered and instance.last_watered:
                process_watering_event(instance)
                
            if old_log.last_fertilized != instance.last_fertilized and instance.last_fertilized:
                process_fertilizing_event(instance)
                
            if old_log.last_pruned != instance.last_pruned and instance.last_pruned:
                process_pruning_event(instance)
                
        except GardenLog.DoesNotExist:
            # Shouldn't happen, but handle just in case
            pass
    
    # Clear relevant caches
    clear_garden_cache(garden)
    
    # Update search index
    if hasattr(settings, 'ENABLE_SEARCH_INDEXING') and settings.ENABLE_SEARCH_INDEXING:
        transaction.on_commit(lambda: reindex_model(GardenLog, [instance.id]))


@receiver(post_delete, sender=GardenLog)
def garden_log_deleted_handler(sender, instance, **kwargs):
    """Handle garden log deletion"""
    garden = instance.garden
    plant = instance.plant
    
    logger.info(f"Plant {plant.common_name or plant.scientific_name if plant else 'Unknown'} "
               f"removed from garden {garden.name or 'Unnamed'} at position "
               f"({instance.x_coordinate}, {instance.y_coordinate})")
    
    # Clear related notifications for this plant in this garden
    try:
        clear_plant_notifications(instance)
    except Exception as e:
        logger.error(f"Failed to clear plant notifications: {e}")
    
    # Clear relevant caches
    clear_garden_cache(garden)


# ==================== HELPER FUNCTIONS ====================

def clear_garden_cache(garden):
    """Clear cache entries related to a garden"""
    # Clear specific garden cache
    cache.delete(f"garden:{garden.id}")
    
    # Clear user's garden list cache
    cache.delete(f"user:{garden.user.id}:gardens")
    
    # Clear dashboard cache
    cache.delete(f"user:{garden.user.id}:garden_dashboard")


def process_health_status_change(old_log, new_log):
    """Process a change in plant health status"""
    if new_log.health_status == PlantHealthStatus.POOR:
        logger.warning(f"Plant health declined to Poor in garden {new_log.garden.id}")
        
        # Create health alert notification
        try:
            notification = Notification.objects.create(
                garden=new_log.garden,
                name="Plant needs attention",
                type=NotifTypes.OT,
                subtype="Health Alert",
                interval=1  # One-time notification
            )
            notification.plants.add(new_log.plant)
            
            # Create immediate notification instance
            NotificationInstance.objects.create(
                notification=notification,
                next_due=timezone.now(),
                status="PENDING",
                message=f"Your {new_log.plant.common_name or 'plant'} needs attention - health is declining"
            )
        except Exception as e:
            logger.error(f"Failed to create health alert notification: {e}")
    
    elif (old_log.health_status in [PlantHealthStatus.POOR, PlantHealthStatus.DYING] and 
          new_log.health_status in [PlantHealthStatus.HEALTHY, PlantHealthStatus.EXCELLENT]):
        logger.info(f"Plant health improved to {new_log.health_status} in garden {new_log.garden.id}")
        
        # Could implement positive reinforcement notifications here


def create_welcome_notification(garden):
    """Create welcome notification for a newly created garden"""
    notification = Notification.objects.create(
        garden=garden,
        name="Welcome to your new garden!",
        type=NotifTypes.OT,
        subtype="Welcome",
        interval=1  # One-time notification
    )
    
    # Create immediate notification instance
    NotificationInstance.objects.create(
        notification=notification,
        next_due=timezone.now(),
        status="PENDING",
        message=f"Your new garden '{garden.name or 'Unnamed'}' is ready for planting!"
    )


def create_plant_care_notifications(garden_log):
    """Create care notifications for a newly added plant"""
    plant = garden_log.plant
    garden = garden_log.garden
    
    # Skip if plant is None
    if not plant:
        return
    
    # Get plant care requirements (if available)
    water_days = getattr(plant, 'watering_frequency', None)
    fertilize_days = getattr(plant, 'fertilizing_frequency', None)
    
    plant_name = plant.common_name or 'plant'
    if len(plant_name) > 85:  # Leave room for "Water " (6 chars) + safety margin
        plant_name = plant_name[:82] + '...'

    # Create watering notification if water_days is available
    if water_days and water_days > 0:
        water_notif = Notification.objects.create(
            garden=garden,
            name=f"Water {plant.common_name or 'plant'}",
            type=NotifTypes.OT,  # Could add a WA type as suggested
            subtype="Watering",
            interval=water_days
        )
        water_notif.plants.add(plant)
        
        # Create first notification instance due in water_days
        NotificationInstance.objects.create(
            notification=water_notif,
            next_due=timezone.now() + timezone.timedelta(days=water_days),
            status="PENDING",
            message=f"Time to water your {plant.common_name or 'plant'}"
        )
    
    # Create fertilizing notification if fertilize_days is available
    if fertilize_days and fertilize_days > 0:
        fert_notif = Notification.objects.create(
            garden=garden,
            name=f"Fertilize {plant.common_name or 'plant'}",
            type=NotifTypes.FE,
            interval=fertilize_days
        )
        fert_notif.plants.add(plant)
        
        # Create first notification instance due in fertilize_days
        NotificationInstance.objects.create(
            notification=fert_notif,
            next_due=timezone.now() + timezone.timedelta(days=fertilize_days),
            status="PENDING",
            message=f"Time to fertilize your {plant.common_name or 'plant'}"
        )


def clear_plant_notifications(garden_log):
    """Clear notifications for a plant when it's removed from garden"""
    plant = garden_log.plant
    garden = garden_log.garden
    
    if not plant:
        return
        
    # Find notifications for this specific plant in this garden
    from django.db.models import Count
    from notifications.models import NotificationPlantAssociation
    
    # Get notifications that only have this plant
    plant_assocs = NotificationPlantAssociation.objects.filter(
        plant=plant,
        notification__garden=garden
    )
    
    # For each association, count how many plants are in that notification
    for assoc in plant_assocs:
        notification = assoc.notification
        plant_count = notification.plants.count()
        
        if plant_count <= 1:
            # This is the only plant in the notification, delete the notification
            notification.delete()
            logger.info(f"Deleted notification {notification.id} after plant removal")
        else:
            # Remove just this plant from the notification
            notification.plants.remove(plant)
            logger.info(f"Removed plant from notification {notification.id}")


def process_watering_event(garden_log):
    """Process a watering event"""
    # Mark related watering notifications as completed
    NotificationInstance.objects.filter(
        notification__garden=garden_log.garden,
        notification__plants=garden_log.plant,
        notification__type=NotifTypes.OT,  # Use WA if implemented
        notification__subtype="Watering",
        status="PENDING"
    ).update(
        status="COMPLETED",
        completed_at=timezone.now()
    )
    
    logger.info(f"Plant {garden_log.plant.id if garden_log.plant else 'Unknown'} "
               f"watered in garden {garden_log.garden.id}")


def process_fertilizing_event(garden_log):
    """Process a fertilizing event"""
    # Mark related fertilizing notifications as completed
    NotificationInstance.objects.filter(
        notification__garden=garden_log.garden,
        notification__plants=garden_log.plant,
        notification__type=NotifTypes.FE,
        status="PENDING"
    ).update(
        status="COMPLETED",
        completed_at=timezone.now()
    )
    
    logger.info(f"Plant {garden_log.plant.id if garden_log.plant else 'Unknown'} "
               f"fertilized in garden {garden_log.garden.id}")


def process_pruning_event(garden_log):
    """Process a pruning event"""
    # Mark related pruning notifications as completed
    NotificationInstance.objects.filter(
        notification__garden=garden_log.garden,
        notification__plants=garden_log.plant,
        notification__type=NotifTypes.PR,
        status="PENDING"
    ).update(
        status="COMPLETED",
        completed_at=timezone.now()
    )
    
    logger.info(f"Plant {garden_log.plant.id if garden_log.plant else 'Unknown'} "
               f"pruned in garden {garden_log.garden.id}")