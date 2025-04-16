# backend/root/user_management/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationInstanceViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-instances', NotificationInstanceViewSet, basename='notification-instance')

urlpatterns = [
    path('', include(router.urls)),
]