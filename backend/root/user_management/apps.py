# backend/root/user_management/apps.py

from django.apps import AppConfig


class UserManagementConfig(AppConfig):
    name = 'user_management'
    verbose_name = 'User Management'

    def ready(self):
        import user_management.signals
