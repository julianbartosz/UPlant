# backend/root/gardens/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from gardens.api.views import GardenViewSet, GardenLogViewSet, WeatherByZipView

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'gardens', GardenViewSet, basename='garden')
router.register(r'garden-logs', GardenLogViewSet, basename='garden-log')

urlpatterns = [
    # Direct weather endpoint
    path('weather/<str:zip_code>/', WeatherByZipView.as_view(), name='weather-by-zip'),
    # Include the router URLs
    path('', include(router.urls)),
]

app_name = 'gardens_api'