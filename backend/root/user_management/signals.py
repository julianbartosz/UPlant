# backend/root/user_management/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from user_management.models import User

@receiver(post_save, sender=User)
def user_created_or_updated(sender, instance, created, **kwargs):
    if created:
        subject = "Welcome to UPlant"
        message = "Your account has been created."
    else:
        subject = "Account Updated"
        message = "Your account information has been updated."

    send_mail(
        subject,
        message,
        'no-reply@uwm.edu',
        [instance.email],
        fail_silently=False,
    )
