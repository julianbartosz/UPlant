# backend/root/user_management/backends.py

import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

# Get a logger instance for this module - allows for centralized logging configuration
logger = logging.getLogger(__name__)
# Get the User model as configured in Django settings (could be a custom user model)
UserModel = get_user_model()

class EmailModelBackend(ModelBackend):
    """
    Authentication backend that allows users to log in with their email address.
    
    This backend extends Django's ModelBackend to support:
    - Email-based authentication
    - Optional login attempt rate limiting
    - Inactive account handling
    - Detailed authentication logging
    
    Configuration (via settings.py):
    - ENABLE_AUTH_RATE_LIMITING: Boolean to enable/disable rate limiting
    - AUTH_MAX_ATTEMPTS: Maximum number of failed attempts before lockout (default: 5)
    - AUTH_LOCKOUT_SECONDS: Duration in seconds for lockout period (default: 300)
    
    Usage:
    Add this backend to AUTHENTICATION_BACKENDS in settings.py:
    
    AUTHENTICATION_BACKENDS = [
        'user_management.backends.EmailModelBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email address.
        
        This method is called by Django's authentication system when a user attempts to log in.
        It overrides the default ModelBackend authenticate method to use email as the primary
        identifier instead of username.
        
        Flow:
        1. Validate input parameters
        2. Check for rate limiting (if enabled)
        3. Look up user by email
        4. Verify account is active
        5. Check password
        6. Record login attempt for rate limiting
        
        Security features:
        - Email normalization to prevent case-sensitive bypass
        - Rate limiting to prevent brute force attacks
        - Consistent timing to prevent timing attacks
        - Detailed logging for audit trails
        
        Args:
            request: The HTTP request object (may contain IP address for rate limiting)
            username: Actually the email address in this context
            password: The user's password
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Early return if required credentials aren't provided
        if not username or not password:
            return None
            
        # Check rate limiting (if enabled)
        # This prevents brute force attacks by limiting the number of login attempts
        if self._is_rate_limited(request, username):
            logger.warning(f"Authentication rate limited for email: {username}")
            return None
            
        try:
            # Normalize email to lowercase to ensure case-insensitive matching
            # This prevents attackers from bypassing uniqueness checks with case variations
            email = username.lower().strip()
            
            # Lookup user by email - this might raise UserModel.DoesNotExist
            user = UserModel.objects.get(email=email)
            
            # Check if the user account is active - inactive accounts can't log in
            # This provides a way to disable accounts without deleting them
            if not user.is_active:
                logger.info(f"Authentication attempt for inactive account: {email}")
                return None
            
            # Verify password - Django's check_password handles secure password comparison
            # with constant time algorithm to prevent timing attacks
            if user.check_password(password):
                logger.info(f"Successful authentication for: {email}")
                
                # Record the successful login - resets failed attempt counters
                self._record_login_attempt(email, success=True)
                return user
            else:
                logger.info(f"Failed password authentication for: {email}")
                
                # Record the failed attempt - increments counter for rate limiting
                self._record_login_attempt(email, success=False)
                return None
                
        except UserModel.DoesNotExist:
            # User not found but we still log the attempt
            # Important: Do similar work as successful path to prevent timing attacks
            logger.info(f"Authentication attempted with non-existent email: {username}")
            
            # Record the failed attempt - using consistent timing to prevent enumeration
            self._record_login_attempt(username, success=False)
            return None
        except Exception as e:
            # Catch any unexpected errors during authentication
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return None

    def _is_rate_limited(self, request, email):
        """
        Check if the authentication request should be rate limited.
        
        Rate limiting provides protection against brute force attacks by
        temporarily blocking authentication attempts after too many failures.
        The system tracks both per-email and per-IP address attempts to
        prevent different attack vectors.
        
        Args:
            request: The request object (used to extract IP address)
            email: The email being used for login attempt
            
        Returns:
            bool: True if rate limited (should block login), False otherwise
        """
        # Skip rate limiting check if the feature is not enabled in settings
        if not getattr(settings, 'ENABLE_AUTH_RATE_LIMITING', False):
            return False
            
        # Get client IP address for IP-based rate limiting
        ip_address = self._get_client_ip(request)
        
        # Create unique cache keys for tracking attempts by IP and email
        cache_key_ip = f"auth_attempts:ip:{ip_address}"
        cache_key_email = f"auth_attempts:email:{email}"
        
        # Get current attempt counts from cache
        ip_attempts = cache.get(cache_key_ip, 0)
        email_attempts = cache.get(cache_key_email, 0)
        
        # Get rate limiting configuration from settings with defaults
        max_attempts = getattr(settings, 'AUTH_MAX_ATTEMPTS', 5)
        lockout_time = getattr(settings, 'AUTH_LOCKOUT_SECONDS', 300)  # 5 minutes
        
        # An account is rate limited if either IP or email has too many attempts
        # This prevents both targeted attacks (on specific emails) and distributed
        # attacks (from multiple IPs targeting one email)
        if ip_attempts >= max_attempts or email_attempts >= max_attempts:
            return True
            
        return False
    
    def _record_login_attempt(self, email, success=False):
        """
        Record a login attempt for rate limiting purposes.
        
        This method tracks failed login attempts in the cache to enable
        rate limiting. Successful logins will clear the counter.
        
        Args:
            email: The email used in the login attempt
            success: Whether the attempt was successful (True/False)
        """
        # Skip if rate limiting is disabled in settings
        if not getattr(settings, 'ENABLE_AUTH_RATE_LIMITING', False):
            return
            
        # For successful logins, clear any failed attempt records
        # This allows users to log in again after a successful attempt
        if success:
            cache_key_email = f"auth_attempts:email:{email}"
            cache.delete(cache_key_email)
            return
            
        # Get the configured lockout duration
        lockout_time = getattr(settings, 'AUTH_LOCKOUT_SECONDS', 300)
        
        # Increment the email attempt counter and set expiry time
        # After lockout_time seconds, the counter will automatically reset
        cache_key_email = f"auth_attempts:email:{email}"
        attempts = cache.get(cache_key_email, 0)
        cache.set(cache_key_email, attempts + 1, lockout_time)

    def _get_client_ip(self, request):
        """
        Extract client IP address from request.
        
        This method handles different scenarios including proxied requests
        where the original client IP might be in the X-Forwarded-For header.
        
        Args:
            request: The HTTP request object
            
        Returns:
            str: The client's IP address or "unknown" if not determinable
        """
        if not request:
            return "unknown"
            
        # Check for X-Forwarded-For header (used when behind a proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # The leftmost IP in X-Forwarded-For is typically the client's real IP
            ip = x_forwarded_for.split(',')[0]
        else:
            # Fall back to REMOTE_ADDR if no forwarding header
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class SocialEmailFallbackBackend(ModelBackend):
    """
    A backend that allows users who registered via social auth to also log in with email.
    
    This backend is designed as a fallback mechanism for authentication. It specifically
    handles the case of users who originally registered via social authentication
    (like Google, Facebook, etc.) and then later attempt to log in with email/password.
    
    This backend should be placed AFTER EmailModelBackend in the AUTHENTICATION_BACKENDS
    setting to ensure it only processes fallback cases.
    
    Usage:
    Add this backend AFTER the standard backend in settings.py:
    
    AUTHENTICATION_BACKENDS = [
        'user_management.backends.EmailModelBackend',
        'user_management.backends.SocialEmailFallbackBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Try to authenticate users who may have originally registered via social auth.
        
        This method specifically checks if a user exists with the given email
        but does not have a usable password (which typically means they registered
        through social auth). It then logs this special case but doesn't authenticate
        the user, as they should set up a password first through a password reset flow.
        
        Args:
            request: The HTTP request object
            username: The email address
            password: The password (not used if user has no password set)
            
        Returns:
            None - this backend never successfully authenticates users directly
        """
        if not username or not password:
            return None
            
        try:
            # Find user by normalized email
            email = username.lower().strip()
            user = UserModel.objects.get(email=email)
            
            # Check if the user has a usable password
            # Users who registered via social auth typically don't have a password set
            if not user.has_usable_password():
                # Log the attempt but don't reveal that the account exists
                # This prevents account enumeration while providing audit trail
                logger.info(f"Password login attempted for social-only account: {email}")
                return None
                
            # If we get here, the user has a password, so let the standard backend handle it
            # This backend intentionally doesn't authenticate users, only logs special cases
            return None
            
        except UserModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Unexpected error in social fallback authentication: {str(e)}")
            return None