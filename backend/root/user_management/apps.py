# backend/root/user_management/apps.py

import logging
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# Configure the logger for this module
logger = logging.getLogger(__name__)

class UserManagementConfig(AppConfig):
    """
    Configuration for the User Management application.
    
    This app handles user authentication, registration, profile management,
    and social authentication integration.
    
    The AppConfig class is Django's way of configuring applications.
    It provides a place for application-specific configuration,
    startup initialization, and metadata.
    """
    # The name of the app as used in settings.INSTALLED_APPS
    name = 'user_management'
    
    # Human-readable name for the app, supports translation
    verbose_name = _('User Management')
    
    def ready(self):
        """
        Initialize the User Management application when Django starts.
        
        The ready() method is called by Django when the application is loaded.
        It's the ideal place to perform initialization tasks like registering
        signal handlers and configuring app-specific settings.
        
        This method:
        1. Registers signal handlers
        2. Sets up search indexing for user models (if enabled)
        3. Configures any required services
        4. Performs startup health checks
        
        Exceptions are caught and logged to prevent application startup failures.
        """
        try:
            # Import signal handlers to register them
            # Django's signal architecture requires the module to be imported
            # for the signal handlers to be registered via the @receiver decorator
            import user_management.signals
            logger.info("User Management signals registered successfully")
            
            # Initialize search indexing (if enabled)
            self._setup_search_indexing()
            
            # Configure authentication backends and security settings
            self._configure_auth_settings()
            
            # Verify required settings are correctly configured
            self._verify_settings()
            
            logger.info("User Management app initialized successfully")
        except Exception as e:
            # Log errors but don't crash the application startup
            logger.error(f"Error initializing User Management app: {e}")
    
    def _setup_search_indexing(self):
        """
        Set up search indexing for user models if enabled.
        
        This method checks if search indexing is enabled in settings and,
        if so, registers the User model with the search service.
        
        The search service allows users to be found via the application's
        search functionality by indexing specified fields.
        
        Fields like username and email are indexed, while sensitive fields 
        like password are explicitly excluded from indexing.
        """
        try:
            # Check if search indexing is enabled in settings
            # Uses getattr with a default value to avoid AttributeError if setting is missing
            if getattr(settings, 'ENABLE_SEARCH_INDEXING', False):
                # Import the search service and User model
                from services.search_service import register_search_models
                from user_management.models import User
                
                # Register User model with search service
                # - fields: Fields to be indexed and made searchable
                # - boost_fields: Fields given higher relevance in search results
                # - exclude_fields: Sensitive fields explicitly excluded from indexing
                register_search_models(
                    User,
                    fields=['username', 'email'],
                    boost_fields={'username': 2.0},  # Username matches are twice as relevant
                    exclude_fields=['password']  # Never index passwords
                )
                logger.info("User models registered for search indexing")
        except ImportError:
            # Search service might not be available in all environments
            logger.info("Search indexing service not available, skipping user search registration")
        except Exception as e:
            # Non-critical error - log warning but continue app initialization
            logger.warning(f"Failed to set up search indexing for users: {e}")
    
    def _configure_auth_settings(self):
        """
        Configure authentication settings and backends.
        
        This method:
        1. Imports custom authentication backends
        2. Validates security settings based on the environment
        3. Logs warnings for insecure configurations in production
        
        Different authentication settings may be appropriate for development
        vs. production environments.
        """
        try:
            # Import custom authentication backend that allows login with email
            from user_management.backends import EmailModelBackend
            
            # Apply different settings based on the environment
            # In development mode (DEBUG=True), we can use less strict settings
            if settings.DEBUG:
                logger.info("Running in DEBUG mode with relaxed authentication settings")
            else:
                # In production, ensure security best practices are followed
                # Check for secure cookie settings to prevent session hijacking
                
                # SESSION_COOKIE_SECURE ensures cookies are only sent over HTTPS
                if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                    logger.warning("SESSION_COOKIE_SECURE is not enabled in production!")
                
                # CSRF_COOKIE_SECURE ensures CSRF tokens are only sent over HTTPS
                if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                    logger.warning("CSRF_COOKIE_SECURE is not enabled in production!")
        except ImportError:
            # Custom authentication backends might not be available
            logger.warning("Could not import authentication backends")
        except Exception as e:
            # Non-critical error - log warning but continue app initialization
            logger.warning(f"Error configuring authentication settings: {e}")
    
    def _verify_settings(self):
        """
        Verify that all required settings are properly configured.
        
        This method checks for the presence of settings that are necessary
        for proper functioning of the User Management app, particularly
        those related to email communication and frontend integration.
        
        It also performs additional checks for optional integrations like
        django-allauth if they're being used.
        """
        # Check for required settings
        required_settings = [
            'DEFAULT_FROM_EMAIL',  # Email address used for sending system emails
            'FRONTEND_URL',        # URL to the frontend app, used in email links
        ]
        
        # Collect any missing settings
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)
                
        # Log warnings for missing settings
        if missing_settings:
            logger.warning(f"Missing recommended settings for User Management: {', '.join(missing_settings)}")
            
        # Check django-allauth configuration if it's being used
        # django-allauth is a popular authentication package that handles
        # registration, login, account management, and social authentication
        if 'allauth' in settings.INSTALLED_APPS:
            # Email verification is an important security feature
            if not getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', None):
                logger.warning("ACCOUNT_EMAIL_VERIFICATION not set for allauth")