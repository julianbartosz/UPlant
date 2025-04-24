# backend/root/user_management/backends.py

import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)
UserModel = get_user_model()

class EmailModelBackend(ModelBackend):
    """
    Authentication backend that allows users to log in with their email address.
    
    This backend extends Django's ModelBackend to support:
    - Email-based authentication
    - Optional login attempt rate limiting
    - Inactive account handling
    - Detailed authentication logging
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email address.
        
        Args:
            request: The request object
            username: Actually the email address in this context
            password: The user's password
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        if not username or not password:
            return None
            
        # Check rate limiting (if enabled)
        if self._is_rate_limited(request, username):
            logger.warning(f"Authentication rate limited for email: {username}")
            return None
            
        try:
            # Normalize email to lowercase
            email = username.lower().strip()
            
            # Lookup user by email
            user = UserModel.objects.get(email=email)
            
            # Check if the user account is active
            if not user.is_active:
                logger.info(f"Authentication attempt for inactive account: {email}")
                return None
            
            # Verify password
            if user.check_password(password):
                logger.info(f"Successful authentication for: {email}")
                
                # Record the successful login
                self._record_login_attempt(email, success=True)
                return user
            else:
                logger.info(f"Failed password authentication for: {email}")
                
                # Record the failed attempt
                self._record_login_attempt(email, success=False)
                return None
                
        except UserModel.DoesNotExist:
            logger.info(f"Authentication attempted with non-existent email: {username}")
            
            # Record the failed attempt (but be careful about timing attacks)
            self._record_login_attempt(username, success=False)
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return None

    def _is_rate_limited(self, request, email):
        """
        Check if the authentication request should be rate limited.
        
        Args:
            request: The request object
            email: The email being used for login
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        # Skip rate limiting check if not enabled in settings
        if not getattr(settings, 'ENABLE_AUTH_RATE_LIMITING', False):
            return False
            
        # Get client IP address
        ip_address = self._get_client_ip(request)
        
        # Check cache for rate limiting
        cache_key_ip = f"auth_attempts:ip:{ip_address}"
        cache_key_email = f"auth_attempts:email:{email}"
        
        # Get attempt counts
        ip_attempts = cache.get(cache_key_ip, 0)
        email_attempts = cache.get(cache_key_email, 0)
        
        # Get rate limiting settings
        max_attempts = getattr(settings, 'AUTH_MAX_ATTEMPTS', 5)
        lockout_time = getattr(settings, 'AUTH_LOCKOUT_SECONDS', 300)  # 5 minutes
        
        # Check if rate limited
        if ip_attempts >= max_attempts or email_attempts >= max_attempts:
            return True
            
        return False
    
    def _record_login_attempt(self, email, success=False):
        """
        Record a login attempt for rate limiting purposes.
        
        Args:
            email: The email used in the login attempt
            success: Whether the attempt was successful
        """
        # Skip if rate limiting is disabled
        if not getattr(settings, 'ENABLE_AUTH_RATE_LIMITING', False):
            return
            
        # Don't increment counters for successful logins
        if success:
            # Clear any failed attempt records on success
            cache_key_email = f"auth_attempts:email:{email}"
            cache.delete(cache_key_email)
            return
            
        # Get the timeout setting
        lockout_time = getattr(settings, 'AUTH_LOCKOUT_SECONDS', 300)
        
        # Increment the email attempt counter
        cache_key_email = f"auth_attempts:email:{email}"
        attempts = cache.get(cache_key_email, 0)
        cache.set(cache_key_email, attempts + 1, lockout_time)

    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        if not request:
            return "unknown"
            
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class SocialEmailFallbackBackend(ModelBackend):
    """
    A backend that allows users who registered via social auth to also log in with email.
    
    This is useful for users who linked their social accounts but later want to use
    email/password authentication as well.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Try to authenticate users who may have originally registered via social auth.
        
        This backend should be placed after the standard EmailModelBackend.
        """
        if not username or not password:
            return None
            
        try:
            # Find user by email
            email = username.lower().strip()
            user = UserModel.objects.get(email=email)
            
            # Check if the user has a usable password
            if not user.has_usable_password():
                # If user has no password (social auth) but tries to login with email,
                # log the attempt but don't reveal that the account exists
                logger.info(f"Password login attempted for social-only account: {email}")
                return None
                
            # If we get here, the user has a password, so let the standard backend handle it
            return None
            
        except UserModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Unexpected error in social fallback authentication: {str(e)}")
            return None