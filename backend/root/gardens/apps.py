# backend/root/gardens/apps.py

import logging
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class GardensConfig(AppConfig):
    """
    Configuration for the Gardens application.
    
    This app manages user garden spaces, including the placement of plants
    in gardens and tracking their health and care activities.
    """
    name = 'gardens'
    verbose_name = _('Garden Management')
    
    def ready(self):
        """
        Initialize the Gardens application.
        
        This method is called when the app is ready. It sets up:
        1. Signal handlers for garden/log events
        2. Cache initialization for garden data
        3. Integration with other system components
        """
        try:
            # Import signal handlers from signals.py to register them
            from gardens import signals
            logger.info("Garden signals registered successfully")
            
            # Register any search indexing for gardens
            self._setup_search_indexing()
            
            # Initialize any needed garden caches
            self._init_garden_cache()
            
            logger.info("Gardens app initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gardens app: {e}")
    
    def _setup_search_indexing(self):
        """Set up search indexing for garden models if enabled."""
        from django.conf import settings
        
        if hasattr(settings, 'ENABLE_SEARCH_INDEXING') and settings.ENABLE_SEARCH_INDEXING:
            try:
                from services.search_service import register_search_models
                from gardens.models import Garden, GardenLog
                
                # Register Garden model for search
                register_search_models(
                    Garden, 
                    fields=['name', 'description', 'location', 'garden_type'],
                    boost_fields={'name': 2.0, 'description': 1.0}
                )
                
                # Register GardenLog model for search
                register_search_models(
                    GardenLog,
                    fields=['notes', 'health_status', 'growth_stage'],
                    boost_fields={'notes': 1.5}
                )
                
                logger.info("Garden models registered for search indexing")
            except ImportError:
                logger.warning("Search service not available, garden search indexing skipped")
    
    def _init_garden_cache(self):
        """Initialize any caching needed for garden data."""
        try:
            from django.core.cache import cache
            
            # Check if the cache backend supports the keys() method
            if hasattr(cache, 'keys'):
                # Clear any stale garden-related cache keys on startup
                garden_cache_keys = cache.keys("garden:*") or []
                if garden_cache_keys:
                    cache.delete_many(garden_cache_keys)
                    logger.info(f"Cleared {len(garden_cache_keys)} garden cache entries on startup")
            else:
                # For backends like LocMemCache that don't support keys()
                logger.info("Cache backend doesn't support key pattern matching, skipping garden cache cleanup")
        except Exception as e:
            logger.warning(f"Failed to initialize garden cache: {e}")