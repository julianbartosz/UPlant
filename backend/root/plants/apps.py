# backend/root/plants/apps.py

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class PlantsConfig(AppConfig):
    name = 'plants'
    verbose_name = 'Plant Management'
    
    def ready(self):
        """
        Initialize app configurations, connect signals, and perform startup tasks.
        This method is called once when the application is ready.
        """
        # Import and connect signals
        try:
            from plants import signals
            logger.info("Plant signals connected successfully")
        except ImportError as e:
            logger.error(f"Failed to import plants signals: {e}")
            
        # Register any model event listeners
        from plants.models import Plant, PlantChangeRequest
        
        # Initialize plant indexing for search (if needed)
        self._setup_search_indexing()
        
        # Register admin customizations
        self._register_admin_customization()
        
        logger.info("Plants app initialized successfully")
        
    def _setup_search_indexing(self):
        """Set up search indexing for plants if search functionality is enabled."""
        from django.conf import settings
        
        if hasattr(settings, 'ENABLE_SEARCH_INDEXING') and settings.ENABLE_SEARCH_INDEXING:
            try:
                from services.search_service import register_search_models
                from plants.models import Plant
                
                register_search_models(Plant, fields=[
                    'common_name', 'scientific_name', 'family', 
                    'detailed_description', 'care_instructions'
                ], boost_fields={
                    'common_name': 2.0, 'scientific_name': 1.5}
                )
                logger.info("Plant search indexing configured")
            except ImportError:
                logger.warning("Search service not available, plant indexing skipped")
    
    def _register_admin_customization(self):
        """Register any admin customizations needed for the plants app."""
        pass