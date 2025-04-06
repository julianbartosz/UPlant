# backend/root/plants/api/views.py

from django.urls import path
from plants.api.views import ListPlantsAPIView, RetrievePlantAPIView
from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(url='plants', permanent=False), name='api-root'),
    path('plants/', ListPlantsAPIView.as_view(), name='list_plants'),
    path('plants/<str:id>/', RetrievePlantAPIView.as_view(), name='retrieve_plant'),
    
]
