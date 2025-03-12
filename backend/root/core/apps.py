# backend/root/core/apps.py

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Core Application'

    def ready(self):
        # Optional: Place for startup code, signals import, or whatever else.
        pass
