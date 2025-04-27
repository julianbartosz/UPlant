# backend/root/notifications/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.api.views import NotificationViewSet, NotificationInstanceViewSet

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'instances', NotificationInstanceViewSet, basename='notification-instance')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
]

app_name = 'notifications_api'