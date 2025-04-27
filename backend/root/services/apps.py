from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class ServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services'
    
    def ready(self):
        """Initialize the Services application."""
        try:
            # No need to import the service modules here since they don't have signal handlers
            logger.info("Services app initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Services app: {e}")