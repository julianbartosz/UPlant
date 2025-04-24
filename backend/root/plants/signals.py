# backend/root/plants/signals.py

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from plants.models import Plant, PlantChangeRequest
from django.utils.text import slugify
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ==================== PLANT SIGNALS ====================

@receiver(pre_save, sender=Plant)
def ensure_plant_has_slug(sender, instance, **kwargs):
    """Ensure plant has a slug before saving"""
    if not instance.slug:
        # Generate a slug from common_name if available, otherwise from scientific_name
        base_name = instance.common_name or instance.scientific_name
        if base_name:
            instance.slug = slugify(base_name)
        else:
            # Fallback to a generic slug if no names are available
            instance.slug = f"plant-{instance.id if instance.id else 'new'}"
            
    # If the slug already exists, make it unique by appending a number
    if instance.id is None:  # Only for new plants
        counter = 1
        original_slug = instance.slug
        while Plant.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1

@receiver(post_save, sender=Plant)
def plant_saved(sender, instance, created, **kwargs):
    """Log plant creation/updates and clear cache"""
    # Clear any cached data related to plants
    cache_keys = [
        'plant_list',
        f'plant_detail_{instance.id}',
        f'plant_detail_slug_{instance.slug}'
    ]
    cache.delete_many(cache_keys)
    
    # Log the action
    if created:
        logger.info(
            f"New plant created: {instance.common_name or instance.scientific_name} "
            f"(ID: {instance.id}) by {instance.created_by}"
        )
    else:
        logger.info(
            f"Plant updated: {instance.common_name or instance.scientific_name} "
            f"(ID: {instance.id})"
        )

# ==================== CHANGE REQUEST SIGNALS ====================

@receiver(post_save, sender=PlantChangeRequest)
def change_request_saved(sender, instance, created, **kwargs):
    """Handle change request creation and status changes"""
    if created:
        # Log new change request
        logger.info(
            f"New change request created for plant {instance.plant.id} "
            f"({instance.plant.common_name}) - Field: {instance.field_name}, "
            f"User: {instance.user}"
        )
        
        # Notify admins about new change requests (if notification system exists)
        if hasattr(settings, 'ENABLE_ADMIN_NOTIFICATIONS') and settings.ENABLE_ADMIN_NOTIFICATIONS:
            from services.notification_service import send_notification
            admin_msg = (
                f"New plant change request from {instance.user.username}: "
                f"'{instance.field_name}' on '{instance.plant.common_name}'"
            )
            send_notification(
                recipients='admin_group', 
                message=admin_msg,
                subject="New Plant Change Request",
                link=f"/admin/plants/plantchangerequest/{instance.id}/change/",
                category="plant_change"
            )
    else:
        # Handle status changes
        if instance.status == 'APPROVED':
            logger.info(
                f"Change request {instance.id} approved by {instance.reviewer} "
                f"for plant {instance.plant.id} ({instance.plant.common_name})"
            )
            
            # Notify the user who submitted the change
            if hasattr(settings, 'ENABLE_USER_NOTIFICATIONS') and settings.ENABLE_USER_NOTIFICATIONS:
                from services.notification_service import send_notification
                user_msg = (
                    f"Your suggested change to {instance.plant.common_name}'s "
                    f"'{instance.field_name}' has been approved!"
                )
                send_notification(
                    recipients=instance.user,
                    message=user_msg,
                    subject="Plant Change Request Approved",
                    link=f"/plants/{instance.plant.slug}",
                    category="plant_change"
                )
                
        elif instance.status == 'REJECTED':
            logger.info(
                f"Change request {instance.id} rejected by {instance.reviewer} "
                f"for plant {instance.plant.id} ({instance.plant.common_name})"
            )
            
            # Notify the user who submitted the change
            if hasattr(settings, 'ENABLE_USER_NOTIFICATIONS') and settings.ENABLE_USER_NOTIFICATIONS:
                from services.notification_service import send_notification
                user_msg = (
                    f"Your suggested change to {instance.plant.common_name}'s "
                    f"'{instance.field_name}' was not approved. "
                    f"Reason: {instance.review_notes or 'No reason provided.'}"
                )
                send_notification(
                    recipients=instance.user,
                    message=user_msg,
                    subject="Plant Change Request Rejected",
                    link=f"/plants/{instance.plant.slug}",
                    category="plant_change"
                )

# ==================== REGISTER SIGNALS ====================
# These are automatically imported when the app is ready