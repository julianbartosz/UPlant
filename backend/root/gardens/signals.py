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
                # Lazy import to avoid circular import
                from services.notification_service import create_welcome_notification
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
                # Lazy import
                from services.notification_service import create_plant_care_notifications
                create_plant_care_notifications(instance)
            except Exception as e:
                logger.error(f"Failed to create plant care notifications: {e}")
    else:
        # Plant log updated
        try:
            old_log = GardenLog.objects.get(pk=instance.pk)
            
            # Check if health status changed
            if old_log.health_status != instance.health_status:
                try:
                    # Lazy import
                    from services.notification_service import handle_health_change
                    handle_health_change(old_log.health_status, instance.health_status, garden, plant)
                except Exception as e:
                    logger.error(f"Failed to handle health change: {e}")
                
            # Check if plant was moved
            if (old_log.x_coordinate != instance.x_coordinate or 
                old_log.y_coordinate != instance.y_coordinate):
                logger.info(f"Plant moved from ({old_log.x_coordinate}, {old_log.y_coordinate}) to "
                           f"({instance.x_coordinate}, {instance.y_coordinate}) in garden {garden.id}")
            
            # Check if care activities were performed
            try:
                # Lazy import
                from services.notification_service import handle_plant_care_event
                
                if old_log.last_watered != instance.last_watered and instance.last_watered:
                    handle_plant_care_event(instance, 'watering')
                    
                if old_log.last_fertilized != instance.last_fertilized and instance.last_fertilized:
                    handle_plant_care_event(instance, 'fertilizing')
                    
                if old_log.last_pruned != instance.last_pruned and instance.last_pruned:
                    handle_plant_care_event(instance, 'pruning')
            except Exception as e:
                logger.error(f"Failed to handle plant care event: {e}")
                
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
        # Lazy import
        from services.notification_service import cleanup_plant_notifications
        cleanup_plant_notifications(garden, plant)
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