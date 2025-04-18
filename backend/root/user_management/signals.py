# backend/root/user_management/signals.py

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
SIGNIFICANT_FIELDS = ['email', 'username', 'is_active']

# ==================== USER ACCOUNT SIGNALS ====================

@receiver(pre_save, sender=User)
def user_about_to_change(sender, instance, **kwargs):
    """Track significant changes to user accounts"""
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
    """Handle user creation and updates"""
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
    """Track user login activity"""
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
    """Track user logout activity"""
    if user:
        try:
            ip_address = get_client_ip(request)
            logger.info(f"User {user.email} logged out from {ip_address}")
        except Exception as e:
            logger.error(f"Error in user_logged_out signal: {str(e)}")


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):
    """Track failed login attempts"""
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
    """Send welcome email to new users"""
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
        
        # Render email templates
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = render_to_string('emails/welcome_email.txt', context)
        
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
    """Send notification when account is reactivated"""
    try:
        subject = "Your UPlant Account Has Been Reactivated"
        
        message = (
            f"Hello {user.username},\n\n"
            f"Your UPlant account has been reactivated. "
            f"You can now log in and access all features again.\n\n"
            f"If you didn't expect this change, please contact support immediately."
        )
        
        send_mail(
            subject,
            message,
            get_from_email(),
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Account reactivation email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send account reactivation email: {str(e)}")


def send_email_changed_notification(user, old_email):
    """Send notification to previous email when address is changed"""
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
    """Get sender email from settings or use default"""
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'uplant.notifications@gmail.com')


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_default_garden(user):
    """Create default garden for new users"""
    try:
        # Check if settings has a flag to skip default garden creation
        if getattr(settings, 'SKIP_DEFAULT_GARDEN_CREATION', False):
            return
            
        # Create a starter garden
        Garden.objects.create(
            user=user,
            name="My First Garden",
            description="Get started by adding plants to your garden!",
            size_x=10,
            size_y=10,
        )
        logger.info(f"Default garden created for user {user.email}")
    except Exception as e:
        logger.error(f"Failed to create default garden: {str(e)}")