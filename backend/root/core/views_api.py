# backend/root/core/views_api.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from user_management.models import Plants
from core.serializers import PlantsSerializer
from django.http import JsonResponse

@api_view(['GET'])
def plants_list(request):
    # Retrieve all plants that are not marked as deleted
    plants = Plants.objects.filter(is_deleted=False)
    serializer = PlantsSerializer(plants, many=True)
    return Response(serializer.data)

def api_root(request):
    """Root API view that lists available endpoints"""
    available_endpoints = {
        'plants': '/api/plants/',
        # Add other API endpoints here as you create them
    }
    return JsonResponse({
        'message': 'Welcome to the UPlant API',
        'version': '1.0',
        'available_endpoints': available_endpoints
    })