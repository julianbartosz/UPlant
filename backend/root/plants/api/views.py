# backend/root/plants/api/views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from plants.api.serializers import PlantSerializer, PlantListResponseSerializer
from services.trefle_service import list_plants, retrieve_plants

logger = logging.getLogger(__name__)

# Add custom authentication class to fix the middleware error
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Do not enforce CSRF for API views
        return

class ListPlantsAPIView(APIView):
    """
    GET /api/v1/plants
    Public endpoint that lists plants using the Trefle API.
    """
    # Add authentication class to fix the get_response error
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def get(self, request, format=None):
        try:
            # Extract search term from query parameters if present
            search_term = request.query_params.get('q', '')
            
            # Call the service function with search parameters if provided
            if search_term:
                trefle_response = list_plants(filters={"q": search_term})
            else:
                trefle_response = list_plants()

            # Expected trefle_response structure: { "data": [...], "links": {...}, "meta": {...} }
            serializer = PlantListResponseSerializer(data=trefle_response)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error("ListPlantsAPIView serialization error: %s", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Error in ListPlantsAPIView: %s", e)
            return Response(
                {"error": "Failed to retrieve plant list."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RetrievePlantAPIView(APIView):
    """
    GET /api/v1/plants/<id>
    Public endpoint that retrieves details for a single plant.
    """
    # Add authentication class to fix the get_response error
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def get(self, request, id, format=None):
        try:
            trefle_response = retrieve_plants(id)
            # Expect trefle_response to include a "data" key with the plant object.
            plant_data = trefle_response.get('data')
            if not plant_data:
                return Response(
                    {"error": "Plant not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = PlantSerializer(data=plant_data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error("RetrievePlantAPIView serialization error: %s", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Error in RetrievePlantAPIView for id %s: %s", id, e)
            return Response(
                {"error": "Failed to retrieve plant."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )