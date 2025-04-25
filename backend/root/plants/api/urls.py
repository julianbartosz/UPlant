# backend/root/plants/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from plants.api.views import (
    ListPlantsAPIView, RetrievePlantAPIView, 
    PlantViewSet, PlantChangeRequestViewSet,
    PlantStatisticsAPIView,
    PlantSearchAPIView, PlantSuggestionsAPIView,
    WeatherCompatiblePlantsAPIView,
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'plants', PlantViewSet, basename='plant')
router.register(r'changes', PlantChangeRequestViewSet, basename='change-request')

urlpatterns = [
    # Weather Compatibility endpoints
    path('plants/weather-compatible-plants/', WeatherCompatiblePlantsAPIView.as_view(), name='weather-compatible-plants'),

    # Search endpoints
    path('search/', PlantSearchAPIView.as_view(), name='plant-search'),
    path('search/suggestions/', PlantSuggestionsAPIView.as_view(), name='plant-search-suggestions'),
    
    # Statistics and dashboards
    path('plants/statistics/', PlantStatisticsAPIView.as_view(), name='plant-statistics'),

    # Trefle API integration endpoints
    path('trefle/plants/', ListPlantsAPIView.as_view(), name='trefle-list-plants'),
    path('trefle/plants/<str:id>/', RetrievePlantAPIView.as_view(), name='trefle-retrieve-plant'),

    # Root API
    path('', include(router.urls)),

    # Include the router URLs
    # This will generate:
    # /plants/ - List/create plants
    # /plants/{pk}/ - Retrieve/update/delete plant
    # /plants/create-custom/ - Create custom plant (from @action)
    # /plants/{pk}/user-update/ - Update user's plant (from @action)
    # /plants/user-plants/ - List user's plants (from @action)
    # /plants/{pk}/submit-change/ - Submit change request (from @action)
    # /plants/{pk}/changes/ - List changes for plant (from @action)
    # /changes/ - List/create change requests
    # /changes/{pk}/ - Retrieve/update/delete change request
    # /changes/{pk}/approve/ - Approve change request (from @action)
    # /changes/{pk}/reject/ - Reject change request (from @action)
    # /changes/user-changes/ - List user's change requests (from @action)
]

# For better API discoverability in the browsable API
app_name = 'plants_api'