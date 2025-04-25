# backend/root/user_management/signals.py
"""
Django Signal Handlers for User Management in UPlant

This module defines signal handlers that respond to user-related events throughout
the application lifecycle. Django signals provide a way to execute code when certain
events happen (like user creation, login, or profile updates).

Signal handlers in this file handle:
1. User creation and welcome emails
2. Account changes and notifications
3. Login/logout tracking and security
4. Default garden creation for new users

These handlers work in the background and don't require direct invocation from views.
They help maintain data integrity, provide user notifications, and enhance security
by monitoring account activities.
"""

import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

from user_management.models import User
from gardens.models import Garden

# Set up logging
logger = logging.getLogger(__name__)

# Track field changes to avoid duplicate notifications
# These fields trigger specific notifications when changed
SIGNIFICANT_FIELDS = ['email', 'username', 'is_active']

# ==================== USER ACCOUNT SIGNALS ====================

@receiver(pre_save, sender=User)
def user_about_to_change(sender, instance, **kwargs):
    """
    Track significant changes to user accounts before saving to database.
    
    This signal handler runs before a User model is saved, comparing the current
    database state with the incoming changes. It stores detected changes as a 
    property on the instance for use in post-save handlers.
    
    Args:
        sender: The model class (User)
        instance: The User instance being saved
        **kwargs: Additional signal arguments
        
    Side Effects:
        - Attaches _changed_fields list to the instance with tuples of (field_name, old_value, new_value)
        - Sets _was_activated flag when user status changes from inactive to active
        
    Note:
        This handler only runs for existing users (where instance.pk exists),
        not for newly created users.
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Store previous values to compare after save
            changed_fields = []
            for field in SIGNIFICANT_FIELDS:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    changed_fields.append((field, old_value, new_value))
            
            # Attach to instance for use in post_save
            instance._changed_fields = changed_fields
            
            # Check specifically for status change from inactive to active
            if not old_instance.is_active and instance.is_active:
                instance._was_activated = True
                
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def user_created_or_updated(sender, instance, created, **kwargs):
    """
    Handle user creation and updates after the database save completes.
    
    This signal handler runs after a User model is saved, performing various
    tasks based on whether the user was newly created or updated. It triggers
    welcome emails, default garden creation, and change notifications.
    
    Args:
        sender: The model class (User)
        instance: The User instance that was saved
        created: Boolean flag indicating if this is a new user (True) or update (False)
        **kwargs: Additional signal arguments
        
    Side Effects:
        - For new users:
          - Sends welcome email
          - Creates default garden
          - Logs user creation
        - For existing users:
          - Sends reactivation notice if account was activated
          - Sends email change notification if email was changed
          - Logs significant field changes
          
    Note:
        This handler is skipped during fixture loading (when raw=True)
    """
    # Skip during fixtures loading
    if kwargs.get('raw', False):
        return
    
    try:
        # Process new users
        if created:
            send_welcome_email(instance)
            create_default_garden(instance)
            logger.info(f"New user created: {instance.email}")
            return
        
        # Process user updates
        changed_fields = getattr(instance, '_changed_fields', [])
        
        # Send account reactivation notice
        if getattr(instance, '_was_activated', False):
            send_account_reactivated_email(instance)
        
        # Only notify of significant changes
        if changed_fields:
            logger.info(f"User {instance.email} updated fields: {[f[0] for f in changed_fields]}")
            
            # Check for email change
            email_change = next((change for change in changed_fields if change[0] == 'email'), None)
            if email_change:
                old_email, new_email = email_change[1], email_change[2]
                send_email_changed_notification(instance, old_email)

    except Exception as e:
        logger.error(f"Error in user_created_or_updated signal: {str(e)}")


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """
    Track user login activity and update last login timestamp.
    
    This signal is triggered whenever a user successfully logs in. It records
    the login event with IP address and user agent information for security
    monitoring and audit trails.
    
    Args:
        sender: The class that sent the signal
        request: The HTTP request object
        user: The User instance who logged in
        **kwargs: Additional signal arguments
        
    Side Effects:
        - Updates user's last_login timestamp
        - Logs login activity with IP address and user agent
    
    Security Notes:
        - IP logging helps identify suspicious login patterns
        - User agent tracking helps detect unusual devices/browsers
        - This data is valuable for security audits and intrusion detection
    """
    try:
        # Update last_login (should happen automatically, but just in case)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log the login
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        logger.info(f"User {user.email} logged in from {ip_address} using {user_agent}")
        
        # Could record login history in a separate model if needed
        
    except Exception as e:
        logger.error(f"Error in user_logged_in signal: {str(e)}")


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """
    Track user logout activity for security monitoring.
    
    This signal is triggered whenever a user logs out. It records the logout
    event with IP address information for security tracking and audit purposes.
    
    Args:
        sender: The class that sent the signal
        request: The HTTP request object
        user: The User instance who logged out (may be None for anonymous users)
        **kwargs: Additional signal arguments
        
    Side Effects:
        - Logs logout activity with IP address
        
    Security Notes:
        - Comparing login/logout IP addresses can help detect session hijacking
        - Unexpected logouts might indicate security issues
    """
    if user:
        try:
            ip_address = get_client_ip(request)
            logger.info(f"User {user.email} logged out from {ip_address}")
        except Exception as e:
            logger.error(f"Error in user_logged_out signal: {str(e)}")


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    """
    Track failed login attempts for security monitoring.
    
    This signal is triggered whenever a login attempt fails. It logs the failed
    attempt, which can be used to detect brute force attacks or account
    enumeration attempts.
    
    Args:
        sender: The class that sent the signal
        credentials: Dict containing the credentials used for the login attempt
        **kwargs: Additional signal arguments
        
    Side Effects:
        - Logs failed login attempt with email/username
        
    Security Enhancement Opportunities:
        - Could implement rate limiting based on failed attempts
        - Could trigger account lockouts after multiple failures
        - Could send admin notifications for suspicious activity
    """
    try:
        # Get email from credentials
        email = credentials.get('email', credentials.get('username', 'unknown'))
        logger.warning(f"Failed login attempt for {email}")
        
        # Could implement security measures like:
        # - Rate limiting
        # - Account lockouts
        # - Admin notifications for multiple failures
        
    except Exception as e:
        logger.error(f"Error in user_login_failed signal: {str(e)}")


# ==================== EMAIL FUNCTIONS ====================

def send_welcome_email(user):
    """
    Send welcome email to newly registered users.
    
    This function prepares and sends a personalized welcome email to users
    who have just created an account. It uses HTML templates with plain text
    fallback for better user experience across email clients.
    
    Args:
        user: The User instance who just registered
        
    Side Effects:
        - Sends welcome email to the user's registered email address
        - Logs success or failure of email sending
        
    Template Context:
        - user: The User instance
        - app_url: The frontend application URL
        - help_email: Email address for support
        
    Email Format:
        - HTML version using welcome_email.html template
        - Plain text fallback using welcome_email.txt template
        - Further fallback to inline text if templates don't exist
    """
    try:
        subject = "Welcome to UPlant"
        
        # Get app URL from settings or use default
        app_url = getattr(settings, 'FRONTEND_URL', 'https://uplant.app')
        
        # Create context for email template
        context = {
            'user': user,
            'app_url': app_url,
            'help_email': getattr(settings, 'HELP_EMAIL', 'support@uplant.app'),
        }
        
        html_message = render_to_string('user_management/email/welcome_email.html', context)
        plain_message = render_to_string('user_management/email/welcome_email.txt', context)
        
        # Use plain template fallback if HTML template doesn't exist
        if not html_message:
            plain_message = (
                f"Welcome to UPlant, {user.username}!\n\n"
                f"Thank you for creating an account. You can now start creating "
                f"and managing your gardens.\n\n"
                f"Get started here: {app_url}\n\n"
                f"Happy gardening!"
            )
            
        send_mail(
            subject,
            plain_message,
            get_from_email(),
            [user.email],
            fail_silently=False,
            html_message=html_message if html_message else None
        )
        
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")


def send_account_reactivated_email(user):
    """
    Send notification when user account is reactivated.
    
    This function sends an email notification when a previously deactivated
    account is reactivated. It alerts the user that their account is now active
    and they can log in again.
    
    Args:
        user: The User instance whose account was reactivated
        
    Side Effects:
        - Sends reactivation notification to the user's email address
        - Logs success or failure of email sending
        
    Security Note:
        This email is important as unexpected reactivations could indicate
        account compromise. The message advises users to contact support
        if they didn't expect the change.
    """
    try:
        subject = "Your UPlant Account Has Been Reactivated"
        
        context = {
            'user': user,
            'app_url': getattr(settings, 'FRONTEND_URL', 'https://uplant.app'),
        }
        
        html_message = render_to_string('user_management/email/account_reactivated.html', context)
        plain_message = render_to_string('user_management/email/account_reactivated.txt', context)
        
        # Fallback if templates don't exist yet
        if not html_message:
            plain_message = (
                f"Hello {user.username},\n\n"
                f"Your UPlant account has been reactivated. "
                f"You can now log in and access all features again.\n\n"
                f"If you didn't expect this change, please contact support immediately."
            )
        
        send_mail(
            subject,
            plain_message,
            get_from_email(),
            [user.email],
            fail_silently=False,
            html_message=html_message if html_message else None
        )
        
        logger.info(f"Account reactivation email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send account reactivation email: {str(e)}")


def send_email_changed_notification(user, old_email):
    """
    Send notification to previous email when address is changed.
    
    This function sends a security notice to the user's old email address when
    they change their email. This helps alert users if someone else changed
    their email without permission.
    
    Args:
        user: The User instance whose email was changed
        old_email: The previous email address
        
    Side Effects:
        - Sends change notification to the user's old email address
        - Logs success or failure of email sending
        
    Security Importance:
        This is a critical security notification as changing an email address
        could be used to take over an account. Sending to the old address
        ensures the original account owner is notified.
    """
    try:
        subject = "Your UPlant Email Address Has Been Changed"
        
        message = (
            f"Hello,\n\n"
            f"The email address for your UPlant account has been changed from "
            f"{old_email} to {user.email}.\n\n"
            f"If you didn't make this change, please contact support immediately."
        )
        
        send_mail(
            subject,
            message,
            get_from_email(),
            [old_email],  # Send to old email address
            fail_silently=False,
        )
        
        logger.info(f"Email change notification sent to {old_email}")
    except Exception as e:
        logger.error(f"Failed to send email change notification: {str(e)}")


# ==================== HELPER FUNCTIONS ====================

def get_from_email():
    """
    Get sender email address from settings or use default.
    
    Returns:
        str: Email address to use as the sender for all user management emails
        
    Note:
        Using a consistent sender email helps with email deliverability and
        allows for proper configuration of SPF, DKIM, and DMARC records.
    """
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'uplant.notifications@gmail.com')


def get_client_ip(request):
    """
    Extract client IP address from request, handling proxy forwarding.
    
    This function attempts to get the real client IP even when behind load
    balancers or proxies by checking the X-Forwarded-For header first.
    
    Args:
        request: The HttpRequest object
        
    Returns:
        str: The client's IP address
        
    Note:
        X-Forwarded-For format is typically "client, proxy1, proxy2, ..."
        so we take the first (leftmost) address as the client IP.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_default_garden(user):
    """
    Create a starter garden for new users with sample plants.
    
    This function provisions a new user's account with a default garden
    and optionally adds a starter plant to help them get started with
    the application. It also creates welcome notifications.
    
    Args:
        user: The newly created User instance
        
    Returns:
        Garden: The created garden instance, or None if creation failed
        
    Side Effects:
        - Creates a Garden object for the user
        - Optionally adds a starter plant to the garden
        - Creates welcome notifications
        - Sets up plant care reminders
        
    Configuration:
        Can be disabled by setting SKIP_DEFAULT_GARDEN_CREATION=True in settings
    """
    try:
        # Check if settings has a flag to skip default garden creation
        if getattr(settings, 'SKIP_DEFAULT_GARDEN_CREATION', False):
            return
            
        # Import Garden model here to avoid circular imports
        from gardens.models import Garden, GardenLog
        from plants.models import Plant

        # Create a starter garden with proper fields from gardens/models.py
        garden = Garden.objects.create(
            user=user,
            name="My First Garden",
            description="Welcome to your first garden! Start adding plants and track their growth.",
            size_x=10,
            size_y=10,
            is_public=False,
            location="Home Garden",
            garden_type="Mixed",
        )
        
        try:
            # Find a beginner-friendly plant if available
            starter_plant = Plant.objects.filter(
                is_verified=True, 
                care_instructions__isnull=False
            ).order_by('?').first()
            
            if starter_plant:
                # Add the plant to the garden at center position
                garden_log = GardenLog.objects.create(
                    garden=garden,
                    plant=starter_plant,
                    x_coordinate=5,  # Center of garden
                    y_coordinate=5,  # Center of garden
                    health_status='Healthy',  # Using PlantHealthStatus choices
                    notes="Your starter plant! Water regularly and watch it grow."
                )
                
                # Create care notifications for the starter plant
                try:
                    from services.notification_service import create_plant_care_notifications
                    create_plant_care_notifications(garden_log)
                except (ImportError, Exception) as e:
                    logger.warning(f"Could not create plant care notifications: {str(e)}")
        except Exception as e:
            # Don't let starter plant creation failure stop the process
            logger.warning(f"Could not create starter plant: {str(e)}")
            
        # Create a welcome notification for the garden using the notification service
        try:
            from services.notification_service import create_welcome_notification
            
            create_welcome_notification(garden)
            logger.info(f"Welcome notification created for garden {garden.id}")
        except (ImportError, Exception) as e:
            # Don't let notification failure stop the process
            logger.warning(f"Could not create welcome notification: {str(e)}")
            
        logger.info(f"Default garden created for user {user.email}")
        return garden
        
    except Exception as e:
        logger.error(f"Failed to create default garden: {str(e)}")
        return None