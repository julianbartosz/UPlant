# backend/root/plants/api/views.py

import logging
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, viewsets, permissions, filters
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend

from services.weather_service import get_garden_weather_insights, WeatherServiceError
from plants.api.serializers import (
    PlantBaseSerializer, PlantDetailSerializer, UserPlantCreateSerializer, 
    UserPlantUpdateSerializer, AdminPlantSerializer, PlantChangeRequestSerializer,
    PlantChangeRequestCreateSerializer, TreflePlantSerializer, 
    TreflePlantListResponseSerializer
)
from services.search_service import perform_search, get_search_suggestions
from plants.models import Plant, PlantChangeRequest

logger = logging.getLogger(__name__)

# Authentication class to handle CSRF exemption
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Do not enforce CSRF for API views
        return

# Custom permissions
class IsAdminOrModerator(permissions.BasePermission):
    """Permission to allow only admins and moderators to access view."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.role in ('Admin', 'Moderator')
        )

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """Permission to allow owners or admins to edit, others to read only."""
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner or admin/moderators
        return (
            obj.created_by == request.user or 
            request.user.is_staff or 
            request.user.role in ('Admin', 'Moderator')
        )

# Trefle API Views
class ListPlantsAPIView(APIView):
    """
    GET /api/plants/trefle/plants
    Public endpoint that lists plants using the Trefle API.
    """
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    
    def get(self, request, format=None):
        try:
            # Extract query parameters
            search_term = request.query_params.get('q', '')
            page = request.query_params.get('page', '1')
            filters = {'page': page}
            
            # Add search term if provided
            if search_term:
                filters["q"] = search_term
                
            # Add other filters if needed
            for param in ['edible', 'vegetable', 'family', 'genus']:
                if param in request.query_params:
                    filters[param] = request.query_params[param]
            
            # Call Trefle API service
            trefle_response = list_plants(filters=filters)

            # Validate and return response
            serializer = TreflePlantListResponseSerializer(data=trefle_response)
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
    GET /api/plants/trefle/plants/{id}
    Public endpoint that retrieves details for a single plant from Trefle.
    """
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    
    def get(self, request, id, format=None):
        try:
            trefle_response = retrieve_plants(id)
            plant_data = trefle_response.get('data')
            
            if not plant_data:
                return Response({"error": "Plant not found."}, status=status.HTTP_404_NOT_FOUND)
                
            serializer = TreflePlantSerializer(data=plant_data)
            if serializer.is_valid():
                return Response({
                    "data": serializer.data,
                    "links": trefle_response.get('links', {})
                }, status=status.HTTP_200_OK)
            else:
                logger.error("RetrievePlantAPIView serialization error: %s", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.exception("Error in RetrievePlantAPIView for id %s: %s", id, e)
            return Response(
                {"error": "Failed to retrieve plant."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Local DB Plant Views
class PlantViewSet(viewsets.ModelViewSet):
    """
    API endpoint for interacting with plants in our database.
    
    list: GET /api/plants/plants/
    retrieve: GET /api/plants/plants/{id}/
    create: POST /api/plants/plants/ (admin only)
    update: PUT /api/plants/plants/{id}/ (admin only)
    partial_update: PATCH /api/plants/plants/{id}/ (admin only)
    destroy: DELETE /api/plants/plants/{id}/ (admin only)
    
    Additional actions:
    - create_user_plant: POST /api/plants/plants/create-custom/
    - user_update: PATCH /api/plants/plants/{id}/user-update/
    - user_plants: GET /api/plants/plants/user-plants/
    - submit_change: POST /api/plants/plants/{id}/submit-change/
    - weather_compatibility: GET /api/plants/plants/{id}/weather-compatibility/
    - seasonal_advice: GET /api/plants/plants/{id}/seasonal-advice/
    - weather_recommendations: GET /api/plants/plants/weather-recommendations/
    """
    queryset = Plant.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_user_created', 'is_verified', 'vegetable', 'edible']
    search_fields = ['common_name', 'scientific_name', 'family', 'genus']
    ordering_fields = ['common_name', 'scientific_name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return custom queryset based on filters"""
        queryset = Plant.objects.all()
        
        # Support for special query parameters
        user_only = self.request.query_params.get('user_created', None)
        verified = self.request.query_params.get('verified', None)
        
        if user_only and user_only.lower() == 'true':
            queryset = queryset.filter(is_user_created=True)
            
        if verified and verified.lower() == 'true':
            queryset = queryset.filter(is_verified=True)
            
        # For user_plants action, filter by created_by
        if self.action == 'user_plants':
            return queryset.filter(created_by=self.request.user)
            
        return queryset
    
    def get_permissions(self):
        """Determine permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Admin-only actions
            return [permissions.IsAuthenticated(), IsAdminOrModerator()]
        elif self.action in ['user_update']:
            # Owner or admin can update
            return [permissions.IsAuthenticated(), IsOwnerOrAdminOrReadOnly()]
        elif self.action in ['create_user_plant', 'user_plants', 'submit_change', 
                            'weather_compatibility', 'seasonal_advice']:
            # Any authenticated user can access these endpoints
            return [permissions.IsAuthenticated()]
        # Everyone can view plants
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create_user_plant':
            return UserPlantCreateSerializer
        elif self.action == 'user_update':
            return UserPlantUpdateSerializer
        elif self.action == 'submit_change':
            return PlantChangeRequestCreateSerializer
        elif self.action in ['create', 'update', 'partial_update'] and (
            self.request.user.is_staff or 
            self.request.user.role in ('Admin', 'Moderator')
        ):
            return AdminPlantSerializer
        elif self.action == 'retrieve':
            return PlantDetailSerializer
        return PlantBaseSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to check permissions"""
        # Only admins can create plants directly
        if not (request.user.is_staff or request.user.role in ('Admin', 'Moderator')):
            return Response(
                {"detail": "You do not have permission to create plants directly."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
        
    @action(detail=False, methods=['post'], url_path='create-custom')
    def create_user_plant(self, request):
        """Endpoint for users to create custom plants."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Context is automatically passed to serializer.create
        plant = serializer.save()
        
        # Return the full plant details
        return Response(
            PlantDetailSerializer(plant, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['patch'], url_path='user-update')
    def user_update(self, request, pk=None):
        """Allow users to update only their own plants or specific fields."""
        plant = self.get_object()
        
        # Check if this is a user trying to edit a Trefle plant
        is_trefle_plant = plant.api_id is not None and not plant.is_user_created
        is_admin = request.user.is_staff or request.user.role in ('Admin', 'Moderator')
        
        # If this is a user trying to edit a Trefle plant, redirect to change request
        if is_trefle_plant and not is_admin:
            return Response(
                {"detail": "You cannot directly edit a Trefle plant. Please submit a change request."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If it's a user's own plant or admin, allow the update
        serializer = self.get_serializer(plant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update the plant (user is passed to consider permissions)
        updated_plant = serializer.save(user=request.user)
        
        # Return the updated plant
        return Response(
            PlantDetailSerializer(updated_plant, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='user-plants')
    def user_plants(self, request):
        """Get plants created by the current user."""
        plants = self.get_queryset()
        page = self.paginate_queryset(plants)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(plants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='submit-change')
    def submit_change(self, request, pk=None):
        """Submit a change request for a plant."""
        plant = self.get_object()
        
        # Only allow change requests for Trefle plants
        if plant.is_user_created:
            return Response(
                {"detail": "Change requests are only for Trefle plants. User plants can be edited directly."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add plant to the data for validation
        data = request.data.copy()
        data['plant'] = plant.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Create the change request with current user
        change_request = PlantChangeRequest.objects.create(
            plant=plant,
            user=request.user,
            field_name=serializer.validated_data['field_name'],
            new_value=serializer.validated_data['new_value'],
            reason=serializer.validated_data.get('reason', ''),
            old_value=getattr(plant, serializer.validated_data['field_name'], '')
        )
        
        # Return the created change request
        return Response(
            PlantChangeRequestSerializer(change_request, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
        
    @action(detail=True, methods=['get'], url_path='changes')
    def plant_changes(self, request, pk=None):
        """Get change requests for a specific plant."""
        # Only admins/moderators can see all changes
        plant = self.get_object()
        
        if not (request.user.is_staff or request.user.role in ('Admin', 'Moderator')):
            # Regular users can only see their own change requests
            change_requests = plant.change_requests.filter(user=request.user)
        else:
            # Admins can see all change requests for the plant
            change_requests = plant.change_requests.all()
        
        # Optionally filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            change_requests = change_requests.filter(status=status_filter.upper())
        
        serializer = PlantChangeRequestSerializer(change_requests, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='weather-compatibility')
    def weather_compatibility(self, request, pk=None):
        """
        Check plant compatibility with current weather conditions in user's location.
        Returns information about whether the current weather is suitable for this plant.
        """
        plant = self.get_object()
        
        # Get ZIP code from query params or user profile
        zip_code = request.query_params.get('zip_code')
        if not zip_code and hasattr(request.user, 'profile') and request.user.profile.zip_code:
            zip_code = request.user.profile.zip_code
            
        if not zip_code:
            return Response(
                {"detail": "Please provide a ZIP code parameter or update your profile with a ZIP code."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Get weather data
            weather_data = get_garden_weather_insights(zip_code)
            
            # Analyze plant compatibility based on weather conditions
            compatibility = {
                "plant": {
                    "id": plant.id,
                    "name": plant.common_name,
                    "scientific_name": plant.scientific_name,
                    "image_url": plant.image_url,
                },
                "current_weather": weather_data["current_weather"],
                "is_compatible": True,  # Default to compatible
                "concerns": [],
                "care_recommendations": []
            }
            
            # Get plant's temperature preferences
            min_temp = getattr(plant, 'min_temperature', None)
            max_temp = getattr(plant, 'max_temperature', None)
            
            # Get current temperature
            current_temp = weather_data["current_weather"]["temperature"]["value"]
            
            # Check temperature compatibility
            if min_temp is not None and current_temp < min_temp:
                compatibility["is_compatible"] = False
                compatibility["concerns"].append({
                    "type": "temperature_low",
                    "severity": "high",
                    "message": f"Current temperature ({current_temp}°C) is below this plant's minimum ({min_temp}°C)"
                })
                compatibility["care_recommendations"].append(
                    "Consider moving this plant indoors or to a warmer location."
                )
                
            if max_temp is not None and current_temp > max_temp:
                compatibility["is_compatible"] = False
                compatibility["concerns"].append({
                    "type": "temperature_high",
                    "severity": "high",
                    "message": f"Current temperature ({current_temp}°C) is above this plant's maximum ({max_temp}°C)"
                })
                compatibility["care_recommendations"].append(
                    "Provide shade and additional water to protect from heat stress."
                )
                
            # Check for frost warnings
            if weather_data["frost_warning"]["frost_risk"]:
                frost_temp = weather_data["frost_warning"]["min_temperature"]
                compatibility["concerns"].append({
                    "type": "frost_warning",
                    "severity": "high",
                    "message": f"Frost expected soon with temperatures as low as {frost_temp}°C"
                })
                compatibility["care_recommendations"].append(
                    "Protect sensitive plants from frost with covers or by moving them indoors."
                )
                
            # Check for extreme heat
            if weather_data["extreme_heat_warning"]["extreme_heat"]:
                max_temp = weather_data["extreme_heat_warning"]["max_temperature"]
                compatibility["concerns"].append({
                    "type": "heat_warning",
                    "severity": "high",
                    "message": f"Extreme heat expected with temperatures up to {max_temp}°C"
                })
                compatibility["care_recommendations"].append(
                    "Ensure adequate watering and shade during the hottest parts of the day."
                )
                
            # Check for watering needed
            if weather_data["watering_needed"]["should_water"]:
                compatibility["concerns"].append({
                    "type": "watering_needed",
                    "severity": "medium",
                    "message": weather_data["watering_needed"]["reason"]
                })
                
                # Add plant-specific watering advice based on its needs
                if hasattr(plant, 'water_interval') and plant.water_interval:
                    compatibility["care_recommendations"].append(
                        f"This plant typically needs watering every {plant.water_interval} days."
                    )
                else:
                    compatibility["care_recommendations"].append(
                        "Water thoroughly, ensuring the soil is moist but not waterlogged."
                    )
            
            # Check for high wind warnings
            if weather_data["high_wind_warning"]["high_winds"]:
                wind_speed = weather_data["high_wind_warning"]["max_wind_speed"]
                compatibility["concerns"].append({
                    "type": "wind_warning",
                    "severity": "medium", 
                    "message": f"High winds expected with speeds up to {wind_speed} km/h"
                })
                compatibility["care_recommendations"].append(
                    "Consider staking tall plants or moving potted plants to protected areas."
                )
                
            # Add forecast summary
            compatibility["forecast_summary"] = weather_data["forecast_summary"]
            
            return Response(compatibility)
            
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"detail": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error analyzing weather compatibility: {str(e)}")
            return Response(
                {"detail": "An error occurred while analyzing plant compatibility."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='seasonal-advice')
    def seasonal_advice(self, request, pk=None):
        """
        Get seasonal gardening advice for a specific plant based on current weather conditions.
        """
        plant = self.get_object()
        
        # Get ZIP code from query params or user profile
        zip_code = request.query_params.get('zip_code')
        if not zip_code and hasattr(request.user, 'profile') and request.user.profile.zip_code:
            zip_code = request.user.profile.zip_code
            
        if not zip_code:
            return Response(
                {"detail": "Please provide a ZIP code parameter or update your profile with a ZIP code."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Get weather data
            weather_data = get_garden_weather_insights(zip_code)
            
            # Determine current season based on temperature patterns
            avg_high = weather_data["forecast_summary"]["average_high"]
            avg_low = weather_data["forecast_summary"]["average_low"]
            
            # Simple season determination based on temperature
            # This is a simplified approach and could be improved with date-based logic
            if avg_high > 25:
                season = "summer"
            elif avg_high > 15:
                if avg_low < 10:
                    season = "spring" if avg_high < 20 else "fall"
                else:
                    season = "summer"
            elif avg_high > 5:
                season = "fall"
            else:
                season = "winter"
            
            # Generate seasonal advice
            seasonal_advice = {
                "plant": {
                    "id": plant.id,
                    "name": plant.common_name,
                    "scientific_name": plant.scientific_name,
                },
                "current_season": season,
                "weather_summary": {
                    "avg_high": avg_high,
                    "avg_low": avg_low,
                    "current_temp": weather_data["current_weather"]["temperature"]["value"],
                },
                "seasonal_tips": [],
                "care_calendar": {}
            }
            
            # Generate plant-specific seasonal tips based on the current season
            if season == "spring":
                seasonal_advice["seasonal_tips"] = [
                    "Begin regular fertilization as growth resumes",
                    "Monitor for early season pests and diseases",
                    "Start gradual sun exposure for indoor plants being moved outdoors"
                ]
                if hasattr(plant, 'maintenance_notes') and 'spring' in plant.maintenance_notes.lower():
                    seasonal_advice["seasonal_tips"].append(f"Plant-specific note: {plant.maintenance_notes}")
                    
                # Check if current temperature is suitable for outdoor planting
                if hasattr(plant, 'min_temperature') and plant.min_temperature > weather_data["current_weather"]["temperature"]["value"]:
                    seasonal_advice["seasonal_tips"].append(
                        f"Wait before planting outdoors - current temperatures are still too low for this plant"
                    )
                    
            elif season == "summer":
                seasonal_advice["seasonal_tips"] = [
                    "Increase watering frequency during hot periods",
                    "Provide afternoon shade for sensitive plants",
                    "Monitor for drought stress and heat damage"
                ]
                if weather_data["extreme_heat_warning"]["extreme_heat"]:
                    seasonal_advice["seasonal_tips"].append(
                        "Extra care needed due to extreme heat forecast"
                    )
                    
            elif season == "fall":
                seasonal_advice["seasonal_tips"] = [
                    "Reduce fertilization as growth slows",
                    "Begin preparations for colder weather",
                    "Consider bringing sensitive plants indoors before first frost"
                ]
                if weather_data["frost_warning"]["frost_risk"]:
                    seasonal_advice["seasonal_tips"].append(
                        f"Frost protection needed - temperatures expected to drop to {weather_data['frost_warning']['min_temperature']}°C"
                    )
                    
            else:  # winter
                seasonal_advice["seasonal_tips"] = [
                    "Minimize watering for dormant plants",
                    "Protect from cold drafts and freezing temperatures",
                    "Monitor humidity levels for indoor plants"
                ]
                if hasattr(plant, 'min_temperature') and plant.min_temperature > 0:
                    seasonal_advice["seasonal_tips"].append(
                        f"This plant is cold-sensitive and should be kept indoors during winter"
                    )
            
            # Add generic care tips based on plant attributes
            if hasattr(plant, 'water_interval') and plant.water_interval:
                seasonal_advice["care_calendar"]["watering"] = f"Every {plant.water_interval} days"
                
            if hasattr(plant, 'sunlight_requirements') and plant.sunlight_requirements:
                seasonal_advice["care_calendar"]["sunlight"] = plant.sunlight_requirements
                
            if hasattr(plant, 'soil_type') and plant.soil_type:
                seasonal_advice["care_calendar"]["soil"] = plant.soil_type
                
            return Response(seasonal_advice)
            
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"detail": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error generating seasonal advice: {str(e)}")
            return Response(
                {"detail": "An error occurred while generating seasonal advice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='weather-recommendations')
    def weather_recommendations(self, request):
        """
        Get plant recommendations based on current weather conditions in user's location.
        Returns a list of plants suitable for the current weather and climate.
        """
        # Get ZIP code from query params or user profile
        zip_code = request.query_params.get('zip_code')
        if not zip_code and hasattr(request.user, 'profile') and request.user.profile.zip_code:
            zip_code = request.user.profile.zip_code
            
        if not zip_code:
            return Response(
                {"detail": "Please provide a ZIP code parameter or update your profile with a ZIP code."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Get weather data
            weather_data = get_garden_weather_insights(zip_code)
            
            # Determine suitable temperature range based on current conditions and forecast
            current_temp = weather_data["current_weather"]["temperature"]["value"]
            avg_high = weather_data["forecast_summary"]["average_high"]
            avg_low = weather_data["forecast_summary"]["average_low"]
            
            # Find plants within this temperature range
            # Add a buffer of 5 degrees in both directions to be more inclusive
            min_temp_threshold = avg_low - 5
            max_temp_threshold = avg_high + 5
            
            suitable_plants = Plant.objects.filter(
                Q(min_temperature__isnull=True) | Q(min_temperature__lte=min_temp_threshold),
                Q(max_temperature__isnull=True) | Q(max_temperature__gte=max_temp_threshold)
            )
            
            # Apply additional filters if provided
            if 'edible' in request.query_params:
                edible = request.query_params.get('edible').lower() == 'true'
                suitable_plants = suitable_plants.filter(edible=edible)
                
            if 'vegetable' in request.query_params:
                vegetable = request.query_params.get('vegetable').lower() == 'true'
                suitable_plants = suitable_plants.filter(vegetable=vegetable)
            
            # Limit results and paginate
            limit = min(int(request.query_params.get('limit', 10)), 50)
            suitable_plants = suitable_plants[:limit]
            
            # Create response with recommendations
            recommendations = {
                "weather_summary": {
                    "current_temperature": current_temp,
                    "avg_high": avg_high,
                    "avg_low": avg_low,
                    "total_rainfall": weather_data["forecast_summary"]["total_rainfall"]
                },
                "recommendations": [],
                "climate_notes": []
            }
            
            # Add climate-specific notes
            if weather_data["frost_warning"]["frost_risk"]:
                recommendations["climate_notes"].append(
                    "Frost is expected in the coming days. Choose cold-tolerant plants or provide protection."
                )
                
            if weather_data["extreme_heat_warning"]["extreme_heat"]:
                recommendations["climate_notes"].append(
                    "Extreme heat is expected. Choose heat-tolerant plants or provide shade and extra watering."
                )
                
            if weather_data["high_wind_warning"]["high_winds"]:
                recommendations["climate_notes"].append(
                    "High winds are expected. Choose wind-resistant plants or provide protection."
                )
                
            # Add recommendations for each plant
            for plant in suitable_plants:
                plant_data = {
                    "id": plant.id,
                    "name": plant.common_name,
                    "scientific_name": plant.scientific_name,
                    "image_url": plant.image_url,
                    "suitability_score": 100,  # Default score
                    "suitability_factors": []
                }
                
                # Calculate suitability score based on temperature preferences
                if plant.min_temperature is not None and plant.max_temperature is not None:
                    # Perfect match - plant temperature range includes current average range
                    if plant.min_temperature <= avg_low and plant.max_temperature >= avg_high:
                        plant_data["suitability_score"] = 100
                        plant_data["suitability_factors"].append("Temperature range is ideal")
                    # Plant can handle the cold but might struggle with heat
                    elif plant.min_temperature <= avg_low and plant.max_temperature < avg_high:
                        factor = max(0, 1 - (avg_high - plant.max_temperature) / 10)
                        plant_data["suitability_score"] = int(70 + (factor * 30))
                        plant_data["suitability_factors"].append("May need protection from high temperatures")
                    # Plant can handle the heat but might struggle with cold
                    elif plant.min_temperature > avg_low and plant.max_temperature >= avg_high:
                        factor = max(0, 1 - (plant.min_temperature - avg_low) / 10)
                        plant_data["suitability_score"] = int(70 + (factor * 30))
                        plant_data["suitability_factors"].append("May need protection from low temperatures")
                    # Plant might struggle with both heat and cold
                    else:
                        plant_data["suitability_score"] = 50
                        plant_data["suitability_factors"].append("Temperature range is challenging")
                
                # Add water requirements compatibility
                if hasattr(plant, 'water_interval') and plant.water_interval:
                    if weather_data["watering_needed"]["should_water"] and plant.water_interval < 7:
                        plant_data["suitability_factors"].append("Requires frequent watering in current dry conditions")
                    elif not weather_data["watering_needed"]["should_water"] and plant.water_interval > 14:
                        plant_data["suitability_factors"].append("Low watering needs match current moist conditions")
                
                recommendations["recommendations"].append(plant_data)
            
            # Sort by suitability score
            recommendations["recommendations"].sort(key=lambda x: x["suitability_score"], reverse=True)
            
            return Response(recommendations)
            
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"detail": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error generating plant recommendations: {str(e)}")
            return Response(
                {"detail": "An error occurred while generating plant recommendations."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlantChangeRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing plant change requests.
    
    list: GET /api/plants/changes/
    retrieve: GET /api/plants/changes/{id}/
    create: POST /api/plants/changes/ 
    update: PUT /api/plants/changes/{id}/ (admin only)
    partial_update: PATCH /api/plants/changes/{id}/ (admin only)
    destroy: DELETE /api/plants/changes/{id}/ (admin only)
    
    Additional actions:
    - approve: POST /api/plants/changes/{id}/approve/
    - reject: POST /api/plants/changes/{id}/reject/
    - user_changes: GET /api/plants/changes/user-changes/
    """
    queryset = PlantChangeRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'field_name', 'plant__common_name']
    ordering_fields = ['created_at', 'updated_at', 'field_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter change requests based on user role."""
        user = self.request.user
        
        if user.is_staff or user.role in ('Admin', 'Moderator'):
            # Admins/moderators can see all change requests
            return PlantChangeRequest.objects.all()
        else:
            # Regular users only see their own requests
            return PlantChangeRequest.objects.filter(user=user)
    
    def get_permissions(self):
        """Determine permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy', 'approve', 'reject']:
            # Admin-only actions
            return [permissions.IsAuthenticated(), IsAdminOrModerator()]
        # Users can create change requests and view their own
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PlantChangeRequestCreateSerializer
        return PlantChangeRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to handle field validation and add user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get related plant
        plant = get_object_or_404(Plant, pk=serializer.validated_data['plant'].id)
        
        # Check if this is a Trefle plant
        if plant.is_user_created:
            return Response(
                {"detail": "Change requests are only for Trefle plants. User plants can be edited directly."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create change request with current user
        field_name = serializer.validated_data['field_name']
        change_request = PlantChangeRequest.objects.create(
            plant=plant,
            user=request.user,
            field_name=field_name,
            new_value=serializer.validated_data['new_value'],
            reason=serializer.validated_data.get('reason', ''),
            old_value=getattr(plant, field_name, '')
        )
        
        response_serializer = PlantChangeRequestSerializer(change_request, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a change request."""
        change_request = self.get_object()
        
        # Only allow approval of pending requests
        if change_request.status != 'PENDING':
            return Response(
                {"detail": f"Cannot approve a request with status '{change_request.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve the request
        change_request.approve(reviewer=request.user)
        
        # Return the updated change request
        serializer = self.get_serializer(change_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a change request."""
        change_request = self.get_object()
        
        # Only allow rejection of pending requests
        if change_request.status != 'PENDING':
            return Response(
                {"detail": f"Cannot reject a request with status '{change_request.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get notes if provided
        notes = request.data.get('notes', '')
        
        # Reject the request
        change_request.reject(reviewer=request.user, notes=notes)
        
        # Return the updated change request
        serializer = self.get_serializer(change_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='user-changes')
    def user_changes(self, request):
        """Get change requests submitted by the current user."""
        changes = PlantChangeRequest.objects.filter(user=request.user)
        
        # Optional status filter
        status_filter = request.query_params.get('status')
        if status_filter:
            changes = changes.filter(status=status_filter.upper())
        
        serializer = self.get_serializer(changes, many=True)
        return Response(serializer.data)

# Statistics and dashboards
class PlantStatisticsAPIView(APIView):
    """
    GET /api/plants/plants/statistics
    Provides statistics about plants in the system.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]

    def get(self, request, format=None):
        """Return statistics about plants."""
        total_plants = Plant.objects.count()
        user_created_plants = Plant.objects.filter(is_user_created=True).count()
        trefle_plants = Plant.objects.filter(api_id__isnull=False).count()
        verified_plants = Plant.objects.filter(is_verified=True).count()
        
        # For admin/moderators, include change request stats
        if request.user.is_staff or request.user.role in ('Admin', 'Moderator'):
            pending_changes = PlantChangeRequest.objects.filter(status='PENDING').count()
            approved_changes = PlantChangeRequest.objects.filter(status='APPROVED').count()
            rejected_changes = PlantChangeRequest.objects.filter(status='REJECTED').count()
            
            return Response({
                'total_plants': total_plants,
                'user_created_plants': user_created_plants,
                'trefle_plants': trefle_plants,
                'verified_plants': verified_plants,
                'pending_changes': pending_changes,
                'approved_changes': approved_changes,
                'rejected_changes': rejected_changes
            })
        
        # For regular users
        user_plants = Plant.objects.filter(created_by=request.user).count()
        user_pending_changes = PlantChangeRequest.objects.filter(
            user=request.user, status='PENDING'
        ).count()
        
        return Response({
            'total_plants': total_plants,
            'user_created_plants': user_created_plants,
            'verified_plants': verified_plants,
            'your_plants': user_plants,
            'your_pending_changes': user_pending_changes
        })

class PlantSearchAPIView(APIView):
    """
    API endpoint for searching plants.
    
    GET /api/plants/search/?q=query_text
    - Searches plants by common_name, scientific_name, family, etc.
    - Returns matching plants
    
    Parameters:
    - q: Search query string
    - order_by: Field to order results by (optional)
    - limit: Maximum number of results (optional)
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    
    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {"detail": "Please provide a search query with the 'q' parameter."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get additional filters from query params
            additional_filters = {}
            for param, value in request.query_params.items():
                if param not in ['q', 'format', 'order_by', 'limit']:
                    additional_filters[param] = value
            
            # Get order_by and limit parameters
            order_by = request.query_params.get('order_by', '-id')
            limit = min(
                int(request.query_params.get('limit', settings.MAX_SEARCH_RESULTS)),
                settings.MAX_SEARCH_RESULTS
            )
            
            # Perform the search
            results = perform_search(
                query_text=query,
                model_class=Plant,
                additional_filters=additional_filters,
                order_by=order_by,
                limit=limit
            )
            
            # Serialize the results
            serializer = PlantBaseSerializer(results, many=True, context={'request': request})
            
            return Response({
                'query': query,
                'count': len(results),
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return Response(
                {"error": "An error occurred during search. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PlantSuggestionsAPIView(APIView):
    """
    API endpoint for getting plant name suggestions for autocomplete.
    
    GET /api/plants/search/suggestions/?q=prefix
    
    Parameters:
    - q: Prefix to get suggestions for (minimum 2 characters)
    - field: Field to get suggestions from (default: common_name)
    - limit: Maximum number of suggestions (default: 10)
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    
    def get(self, request, format=None):
        prefix = request.query_params.get('q', '')
        if not prefix or len(prefix) < 2:
            return Response(
                {"detail": "Please provide a prefix with at least 2 characters using the 'q' parameter."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get field to suggest from (default to common_name)
        field = request.query_params.get('field', 'common_name')
        limit = int(request.query_params.get('limit', 10))
        
        # Get suggestions
        suggestions = get_search_suggestions(
            prefix=prefix,
            model_class=Plant,
            field=field,
            limit=limit
        )
        
        return Response({
            'prefix': prefix,
            'count': len(suggestions),
            'suggestions': suggestions
        })

class WeatherCompatiblePlantsAPIView(APIView):
    """
    GET /api/plants/weather-compatible-plants/
    Find plants compatible with current weather conditions.
    
    Parameters:
    - zip_code: ZIP code for weather data (optional if user profile has one)
    - type: Type of plants to find (vegetables, flowers, etc.)
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    
    def get(self, request, format=None):
        # Get ZIP code from query params or user profile
        zip_code = request.query_params.get('zip_code')
        if not zip_code and hasattr(request.user, 'profile') and request.user.profile.zip_code:
            zip_code = request.user.profile.zip_code
            
        if not zip_code:
            return Response(
                {"detail": "Please provide a ZIP code parameter or update your profile with a ZIP code."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get plant type filter if provided
        plant_type = request.query_params.get('type', None)
        
        try:
            # Get weather data
            weather_data = get_garden_weather_insights(zip_code)
            
            # Get current weather conditions
            current_temp = weather_data["current_weather"]["temperature"]["value"]
            avg_high = weather_data["forecast_summary"]["average_high"]
            avg_low = weather_data["forecast_summary"]["average_low"]
            has_frost_risk = weather_data["frost_warning"]["frost_risk"]
            has_extreme_heat = weather_data["extreme_heat_warning"]["extreme_heat"]
            
            # Find compatible plants
            plants = Plant.objects.all()
            
            # Filter by type if provided
            if plant_type:
                if plant_type == 'vegetables':
                    plants = plants.filter(vegetable=True)
                elif plant_type == 'edible':
                    plants = plants.filter(edible=True)
                
            # Filter by temperature compatibility
            # Plants with minimum temperature below the current low and maximum above the current high
            plants = plants.filter(
                Q(min_temperature__isnull=True) | Q(min_temperature__lt=current_temp),
                Q(max_temperature__isnull=True) | Q(max_temperature__gt=current_temp)
            )
            
            # Add frost risk filter if needed
            if has_frost_risk:
                # Only include frost-resistant plants or those with minimum temperature below 0
                plants = plants.filter(
                    Q(frost_resistant=True) | 
                    Q(min_temperature__isnull=True) | 
                    Q(min_temperature__lt=0)
                )
            
            # Add heat filter if needed
            if has_extreme_heat:
                # Only include heat-tolerant plants
                plants = plants.filter(
                    Q(heat_tolerant=True) | 
                    Q(max_temperature__isnull=True) | 
                    Q(max_temperature__gt=35)  # Arbitrary threshold for extreme heat
                )
            
            # Serialize the results
            serializer = PlantBaseSerializer(plants[:50], many=True, context={'request': request})
            
            return Response({
                'weather_summary': {
                    'current_temp': current_temp,
                    'avg_high': avg_high,
                    'avg_low': avg_low,
                    'frost_risk': has_frost_risk,
                    'extreme_heat': has_extreme_heat
                },
                'compatible_plants': serializer.data,
                'count': len(serializer.data),
                'total_found': plants.count()  # Total before pagination
            })
            
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"detail": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error finding compatible plants: {str(e)}")
            return Response(
                {"detail": "An error occurred while finding compatible plants."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )