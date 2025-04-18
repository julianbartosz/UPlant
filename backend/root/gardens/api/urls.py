# backend/root/gardens/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from gardens.api.views import GardenViewSet, GardenLogViewSet

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'gardens', GardenViewSet, basename='garden')
router.register(r'garden-logs', GardenLogViewSet, basename='garden-log')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
]

app_name = 'gardens_api'