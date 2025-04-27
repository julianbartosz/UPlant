import logging
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification, NotificationInstance, NotifTypes
from gardens.models import PlantHealthStatus

logger = logging.getLogger(__name__)

def send_notification(
    garden=None, 
    recipients=None, 
    plants=None, 
    subject=None,
    message=None, 
    notification_type="OT", 
    subtype=None, 
    interval=1,
    link=None,  # Still accept link but handle differently
    category=None,  # Still accept category but handle differently
    due_date=None
):
    """
    Central service for creating notifications across the app.
    
    Args:
        garden: Garden this notification applies to
        recipients: User or user group receiving the notification
        plants: List of plants this notification relates to
        subject: Notification title/name
        message: Content of the notification
        notification_type: Type code (OT, WA, FE, PR)
        subtype: Subtype (only used with OT type)
        interval: Days between recurring notifications (1 for one-time)
        link: Related URL to visit (will be added to message)
        category: Category for grouping notifications (logged but not stored)
        due_date: When notification is due (default: now)
    """
    try:
        # Handle user recipients vs garden
        if recipients and not garden:
            # Find the user's primary garden or first garden
            from gardens.models import Garden
            if hasattr(recipients, 'gardens'):
                garden = recipients.gardens.first()
        
        # Validate we have a garden
        if not garden:
            logger.error("Cannot create notification without garden")
            return None
            
        # Set notification name/title from subject
        name = subject or "Notification"
        
        # Validate notification type
        valid_types = [choice[0] for choice in NotifTypes.choices]
        if notification_type not in valid_types:
            logger.warning(f"Invalid notification type '{notification_type}', using OT")
            notification_type = "OT"
            
        # Only use subtype with OT type
        if notification_type != "OT" and subtype:
            logger.warning(f"Subtype '{subtype}' ignored for non-Other notification type")
            subtype = None
        elif notification_type == "OT" and not subtype:
            # Default subtype for OT notifications
            subtype = "general"
            
        # Normalize subtype to lowercase with hyphens
        if subtype:
            subtype = subtype.lower().replace(" ", "-")
            
        # Create notification without link and category fields
        notification = Notification.objects.create(
            garden=garden,
            name=name,
            type=notification_type,
            subtype=subtype,
            interval=interval
        )
        
        # Add plants if specified
        if plants:
            if not isinstance(plants, list) and not isinstance(plants, set):
                plants = [plants]
            for plant in plants:
                notification.plants.add(plant)
        
        # Set due date
        if not due_date:
            due_date = timezone.now()
        
        # If link was provided, append it to the message
        enhanced_message = message or name
        if link:
            enhanced_message = f"{enhanced_message}\n\nLink: {link}"
            
        # Log category information for potential future use
        if category:
            logger.info(f"Notification {notification.id} category: {category}")
            
        # Create notification instance
        instance = NotificationInstance.objects.create(
            notification=notification,
            next_due=due_date,
            status="PENDING",
            message=enhanced_message
        )
        
        logger.info(f"Created notification '{name}' (ID: {notification.id})")
        return notification
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None


# ==================== HELPER FUNCTIONS FOR COMMON NOTIFICATION TYPES ====================

def create_welcome_notification(garden):
    """Create welcome notification for a newly created garden"""
    return send_notification(
        garden=garden,
        subject="Welcome to your new garden!",
        message=f"Your new garden '{garden.name or 'Unnamed'}' is ready for planting!",
        notification_type="OT",
        subtype="welcome",
        interval=1
    )


def create_watering_notification(garden, plant, days=7):
    """Create watering notification for a plant"""
    due_date = timezone.now() + timedelta(days=days)
    return send_notification(
        garden=garden,
        plants=plant,
        subject=f"Water {plant.common_name or 'plant'}",
        message=f"Time to water your {plant.common_name or 'plant'}",
        notification_type="WA",  # Use dedicated water type
        interval=days,
        due_date=due_date
    )


def create_fertilizing_notification(garden, plant, days=30):
    """Create fertilizing notification for a plant"""
    due_date = timezone.now() + timedelta(days=days)
    return send_notification(
        garden=garden,
        plants=plant,
        subject=f"Fertilize {plant.common_name or 'plant'}",
        message=f"Time to fertilize your {plant.common_name or 'plant'}",
        notification_type="FE",
        interval=days,
        due_date=due_date
    )


def create_pruning_notification(garden, plant, days=90):
    """Create pruning notification for a plant"""
    due_date = timezone.now() + timedelta(days=days)
    return send_notification(
        garden=garden,
        plants=plant,
        subject=f"Prune {plant.common_name or 'plant'}",
        message=f"Time to prune your {plant.common_name or 'plant'}",
        notification_type="PR",
        interval=days,
        due_date=due_date
    )


def create_health_alert(garden, plant):
    """Create health alert notification for a plant with poor health"""
    return send_notification(
        garden=garden,
        plants=plant,
        subject=f"{plant.common_name or 'Plant'} needs attention",
        message=f"Your {plant.common_name or 'plant'} needs attention - health is declining",
        notification_type="OT",
        subtype="health-alert",
        interval=1
    )


def create_health_improvement_notification(garden, plant):
    """Create positive reinforcement notification for improved plant health"""
    return send_notification(
        garden=garden,
        plants=plant,
        subject="Plant health improved",
        message=f"Great job! Your {plant.common_name or 'plant'} is looking healthier!",
        notification_type="OT",
        subtype="health-improvement",
        interval=1
    )


# ==================== EVENT HANDLERS ====================

def handle_plant_care_event(garden_log, care_type):
    """Handle care event (watering, fertilizing, pruning)"""
    garden = garden_log.garden
    plant = garden_log.plant
    
    if not plant:
        return
    
    # Map care types to notification types
    type_mapping = {
        'watering': 'WA',
        'fertilizing': 'FE',
        'pruning': 'PR'
    }
    
    notification_type = type_mapping.get(care_type)
    if not notification_type:
        logger.error(f"Unknown care type: {care_type}")
        return
    
    # Mark relevant notifications as completed
    instances = NotificationInstance.objects.filter(
        notification__garden=garden,
        notification__plants=plant,
        notification__type=notification_type,
        status="PENDING"
    )
    
    for instance in instances:
        instance.status = "COMPLETED"
        instance.completed_at = timezone.now()
        instance.save()
        
    logger.info(f"Marked {instances.count()} {care_type} notifications as completed for plant {plant.id}")


def handle_health_change(old_status, new_status, garden, plant):
    """Handle changes in plant health status"""
    # Declining health
    if new_status == PlantHealthStatus.POOR:
        logger.warning(f"Plant health declined to Poor in garden {garden.id}")
        # Check if we already have a health alert for this plant
        existing_alert = Notification.objects.filter(
            garden=garden,
            plants=plant,
            type="OT",
            subtype="health-alert"
        ).exists()
        
        if not existing_alert:
            create_health_alert(garden, plant)
    
    # Improving health
    elif (old_status in [PlantHealthStatus.POOR, PlantHealthStatus.DYING] and 
          new_status in [PlantHealthStatus.HEALTHY, PlantHealthStatus.EXCELLENT]):
        logger.info(f"Plant health improved to {new_status} in garden {garden.id}")
        create_health_improvement_notification(garden, plant)


def create_plant_care_notifications(garden_log):
    """Create all care notifications for a newly added plant"""
    plant = garden_log.plant
    garden = garden_log.garden
    
    if not plant:
        return
    
    # Get plant care requirements (if available)
    water_days = getattr(plant, 'watering_frequency', None)
    fertilize_days = getattr(plant, 'fertilizing_frequency', None)
    pruning_days = getattr(plant, 'pruning_frequency', None)
    
    # Create watering notification if watering frequency is available
    if water_days and water_days > 0:
        create_watering_notification(garden, plant, water_days)
    
    # Create fertilizing notification if fertilizing frequency is available
    if fertilize_days and fertilize_days > 0:
        create_fertilizing_notification(garden, plant, fertilize_days)
    
    # Create pruning notification if pruning frequency is available
    if pruning_days and pruning_days > 0:
        create_pruning_notification(garden, plant, pruning_days)


def cleanup_plant_notifications(garden, plant):
    """Clean up notifications when a plant is removed from garden"""
    if not plant:
        return
    
    from notifications.models import NotificationPlantAssociation
    
    # Find notifications for this specific plant in this garden
    plant_assocs = NotificationPlantAssociation.objects.filter(
        plant=plant,
        notification__garden=garden
    )
    
    # For each association, check if this is the only plant
    for assoc in plant_assocs:
        notification = assoc.notification
        plant_count = notification.plants.count()
        
        if plant_count <= 1:
            # This is the only plant in the notification, delete it
            notification.delete()
            logger.info(f"Deleted notification {notification.id} after plant removal")
        else:
            # Other plants exist, just remove this plant
            notification.plants.remove(plant)
            logger.info(f"Removed plant from notification {notification.id}")