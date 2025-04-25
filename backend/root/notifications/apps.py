# backend/root/notifications/apps.py

import logging
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class NotificationsConfig(AppConfig):
    """
    Configuration for the Notifications application.
    
    This app manages garden task notifications, reminders for plant care,
    and scheduling of recurring garden activities.
    """
    name = 'notifications'
    verbose_name = _('Notification Management')
    
    def ready(self):
        """
        Initialize the Notifications application.
        
        This method is called when the app is ready. It sets up:
        1. Signal handlers for notification events
        2. Cache initialization for notification data
        3. Search indexing for notification models
        """
        try:
            from services import notification_service

            # Import signal handlers to register them
            from notifications import signals
            logger.info("Notification signals registered successfully")
            
            # Register search indexing for notifications
            self._setup_search_indexing()
            
            # Initialize notification cache
            self._init_notification_cache()
            
            # Set up any scheduled tasks for checking overdue notifications
            self._setup_scheduled_tasks()
            
            logger.info("Notifications app initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Notifications app: {e}")
    
    def _setup_search_indexing(self):
        """Set up search indexing for notification models if enabled"""
        from django.conf import settings
        
        if hasattr(settings, 'ENABLE_SEARCH_INDEXING') and settings.ENABLE_SEARCH_INDEXING:
            try:
                from services.search_service import register_search_models
                from notifications.models import Notification, NotificationInstance
                
                # Register Notification model for search
                register_search_models(
                    Notification,
                    fields=['name', 'subtype', 'type'],
                    boost_fields={'name': 2.0}
                )
                
                logger.info("Notification models registered for search indexing")
            except ImportError:
                logger.warning("Search service not available, notification search indexing skipped")
    
    def _init_notification_cache(self):
        """Initialize notification cache system"""
        try:
            from django.core.cache import cache
            
            # Check if the cache backend supports the keys() method
            if hasattr(cache, 'keys'):
                # Clear any stale notification-related cache keys on startup
                notification_cache_keys = cache.keys("notification:*") or []
                user_notification_keys = cache.keys("user:*:notification_dashboard") or []
                garden_notification_keys = cache.keys("garden:*:notifications") or []
                
                stale_keys = notification_cache_keys + user_notification_keys + garden_notification_keys
                
                if stale_keys:
                    cache.delete_many(stale_keys)
                    logger.info(f"Cleared {len(stale_keys)} notification cache entries on startup")
            else:
                # For backends like LocMemCache that don't support keys()
                logger.info("Cache backend doesn't support key pattern matching, skipping notification cache cleanup")
        except Exception as e:
            logger.warning(f"Failed to initialize notification cache: {e}")
    
    def _setup_scheduled_tasks(self):
        """Set up any periodic tasks for checking notifications"""
        try:
            from django.conf import settings
            
            if hasattr(settings, 'ENABLE_NOTIFICATION_SCHEDULER') and settings.ENABLE_NOTIFICATION_SCHEDULER:
                # Register periodic tasks for notification processing
                logger.info("Notification scheduler enabled")
                
                # from notifications.tasks import check_overdue_notifications
                # from django_q.tasks import schedule
                # schedule('notifications.tasks.check_overdue_notifications',
                #          schedule_type='I',
                #          minutes=30)
                
        except Exception as e:
            logger.warning(f"Failed to set up notification scheduled tasks: {e}")