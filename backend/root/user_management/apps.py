# backend/root/user_management/apps.py

import logging
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.conf import settings

logger = logging.getLogger(__name__)

class UserManagementConfig(AppConfig):
    """
    Configuration for the User Management application.
    
    This app handles user authentication, registration, profile management,
    and social authentication integration.
    """
    name = 'user_management'
    verbose_name = _('User Management')
    
    def ready(self):
        """
        Initialize the User Management application when Django starts.
        
        This method:
        1. Registers signal handlers
        2. Sets up search indexing for user models (if enabled)
        3. Configures any required services
        4. Performs startup health checks
        """
        try:
            # Import signal handlers to register them
            import user_management.signals
            logger.info("User Management signals registered successfully")
            
            # Initialize search indexing (if enabled)
            self._setup_search_indexing()
            
            # Configure authentication backends
            self._configure_auth_settings()
            
            # Verify required settings
            self._verify_settings()
            
            logger.info("User Management app initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing User Management app: {e}")
    
    def _setup_search_indexing(self):
        """Set up search indexing for user models if enabled"""
        try:
            # Check if search indexing is enabled in settings
            if getattr(settings, 'ENABLE_SEARCH_INDEXING', False):
                from services.search_service import register_search_models
                from user_management.models import User
                
                # Register User model with search service
                register_search_models(
                    User,
                    fields=['username', 'email'],
                    boost_fields={'username': 2.0},
                    exclude_fields=['password']
                )
                logger.info("User models registered for search indexing")
        except ImportError:
            logger.info("Search indexing service not available, skipping user search registration")
        except Exception as e:
            logger.warning(f"Failed to set up search indexing for users: {e}")
    
    def _configure_auth_settings(self):
        """Configure authentication settings and backends"""
        try:
            # Import auth backends if needed
            from user_management.backends import EmailModelBackend
            
            # You could dynamically adjust authentication settings here
            # For example, setting session cookie settings based on environment
            if settings.DEBUG:
                logger.info("Running in DEBUG mode with relaxed authentication settings")
            else:
                # In production, ensure secure settings
                if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                    logger.warning("SESSION_COOKIE_SECURE is not enabled in production!")
                
                if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                    logger.warning("CSRF_COOKIE_SECURE is not enabled in production!")
        except ImportError:
            logger.warning("Could not import authentication backends")
        except Exception as e:
            logger.warning(f"Error configuring authentication settings: {e}")
    
    def _verify_settings(self):
        """Verify that all required settings are properly configured"""
        # Check for required settings
        required_settings = [
            'DEFAULT_FROM_EMAIL',  # For sending emails
            'FRONTEND_URL',        # For links in emails
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)
                
        if missing_settings:
            logger.warning(f"Missing recommended settings for User Management: {', '.join(missing_settings)}")
            
        # Check allauth configuration if being used
        if 'allauth' in settings.INSTALLED_APPS:
            if not getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', None):
                logger.warning("ACCOUNT_EMAIL_VERIFICATION not set for allauth")