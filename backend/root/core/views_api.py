# core/views_api.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from user_management.models import Plants
from core.serializers import PlantsSerializer

@api_view(['GET'])
def plants_list(request):
    # Retrieve all plants that are not marked as deleted
    plants = Plants.objects.filter(is_deleted=False)
    serializer = PlantsSerializer(plants, many=True)
    return Response(serializer.data)
