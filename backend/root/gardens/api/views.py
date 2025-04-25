# backend/root/gardens/api/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from gardens.models import Garden, GardenLog
from gardens.api.serializers import GardenSerializer, GardenLogSerializer, GardenGridSerializer
from notifications.models import Notification, NotificationInstance
from services.weather_service import get_garden_weather_insights, WeatherServiceError
from django.db.models import Count, Sum, Q
from django.utils import timezone
import logging
from django.core.exceptions import ValidationError, PermissionDenied

# Set up logging
logger = logging.getLogger(__name__)

# Authentication class to handle CSRF exemption
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Do not enforce CSRF for API views
        return
    
# delete health status code
class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of a garden to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the garden owner
        return obj.user == request.user


class GardenViewSet(viewsets.ModelViewSet):
    """API endpoint for Gardens"""
    serializer_class = GardenSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    
    def get_queryset(self):
        """Return only gardens belonging to the current user"""
        return Garden.objects.filter(user=self.request.user, is_deleted=False)
    
    def update(self, request, *args, **kwargs):
        """Override the update method to handle garden dimension changes safely"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # Track the original dimensions
            original_size_x = instance.size_x
            original_size_y = instance.size_y
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Save the updated garden
            garden = serializer.save()
            
            # Check if dimensions changed
            size_changed = (original_size_x != garden.size_x or original_size_y != garden.size_y)
            
            if size_changed:
                try:
                    # Handle grid adjustment if dimensions changed
                    self._adjust_grid_for_new_dimensions(
                        garden, 
                        original_size_x, 
                        original_size_y
                    )
                except Exception as e:
                    logger.error(f"Error adjusting grid after dimension change: {str(e)}")
                    return Response(
                        {
                            "garden": serializer.data,
                            "warning": "Garden was updated but grid adjustment failed. You may need to reset your garden grid."
                        }, 
                        status=status.HTTP_200_OK
                    )
            
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Unexpected error in garden update: {str(e)}")
            return Response(
                {"detail": "Garden was updated but an error occurred in processing the response."},
                status=status.HTTP_200_OK
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests by setting partial=True"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def _adjust_grid_for_new_dimensions(self, garden, old_size_x, old_size_y):
        """
        Adjust the garden grid when dimensions change
        This will keep plants that are still within bounds and remove those that are out of bounds
        """
        # Get all plant logs for this garden
        logs = GardenLog.objects.filter(garden=garden)
        
        # Identify logs that are now out of bounds
        out_of_bounds = logs.filter(
            Q(x_coordinate__gte=garden.size_x) | Q(y_coordinate__gte=garden.size_y)
        )
        
        # Delete out of bounds logs
        if out_of_bounds.exists():
            logger.warning(f"Deleting {out_of_bounds.count()} out-of-bounds plants due to garden resize")
            out_of_bounds.delete()
    
    def _get_garden_weather_data(self, garden, user=None):
        """
        Helper method to get weather data for a garden
        Uses the garden owner's zip code from their profile
        """
        user = user or garden.user
        zip_code = None
        
        # Get zip code from user profile only
        if hasattr(user, 'profile') and user.profile and hasattr(user.profile, 'zip_code'):
            zip_code = user.profile.zip_code
        
        if not zip_code:
            return None
            
        try:
            return get_garden_weather_insights(zip_code)
        except WeatherServiceError as e:
            logger.error(f"Weather service error for garden {garden.id}: {str(e)}")
            return None
    
    @action(detail=True, methods=['get'])
    def grid(self, request, pk=None):
        """Return the garden in grid format for the frontend"""
        garden = self.get_object()
        serializer = GardenGridSerializer(garden)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def weather(self, request, pk=None):
        """Get weather data and insights specific to this garden"""
        garden = self.get_object()
        
        # Get zip code from request params, garden, or user profile
        zip_code = request.query_params.get('zip_code')
        
        if not zip_code:
            # Try to get from user
            if hasattr(request.user, 'profile') and request.user.profile.zip_code:
                zip_code = request.user.profile.zip_code
        
        if not zip_code:
            return Response(
                {"detail": "No location information available. Please provide a zip_code parameter or update your profile."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            weather_data = get_garden_weather_insights(zip_code)
            
            # Add garden-specific recommendations based on plants in the garden
            plant_recommendations = self._generate_plant_weather_recommendations(garden, weather_data)
            weather_data["plant_recommendations"] = plant_recommendations
            
            return Response(weather_data)
            
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"detail": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    def _generate_plant_weather_recommendations(self, garden, weather_data):
        """
        Generate plant-specific recommendations based on current weather
        """
        recommendations = []
        garden_logs = garden.logs.select_related('plant').all()
        
        # Get weather conditions that might affect plants
        frost_warning = weather_data.get('frost_warning', {}).get('frost_risk', False)
        extreme_heat = weather_data.get('extreme_heat_warning', {}).get('extreme_heat', False)
        high_winds = weather_data.get('high_wind_warning', {}).get('high_winds', False)
        should_water = weather_data.get('watering_needed', {}).get('should_water', False)
        
        # Generate recommendations for each plant
        for log in garden_logs:
            plant = log.plant
            plant_recs = []
            
            # Frost protection recommendations
            if frost_warning and hasattr(plant, 'frost_resistant') and not plant.frost_resistant:
                plant_recs.append({
                    "type": "frost_protection",
                    "message": f"Protect {plant.common_name} from frost with covers or bring indoors if possible."
                })
            
            # Heat protection recommendations
            if extreme_heat and hasattr(plant, 'heat_tolerant') and not plant.heat_tolerant:
                plant_recs.append({
                    "type": "heat_protection",
                    "message": f"Provide shade for {plant.common_name} during the hottest part of the day."
                })
            
            # Wind protection recommendations
            if high_winds and hasattr(plant, 'staking_required') and plant.staking_required:
                plant_recs.append({
                    "type": "wind_protection",
                    "message": f"Check supports for {plant.common_name} as high winds are expected."
                })
            
            # Watering recommendations
            if should_water and hasattr(plant, 'water_needs'):
                if plant.water_needs == 'high':
                    plant_recs.append({
                        "type": "watering",
                        "message": f"{plant.common_name} has high water needs. Water thoroughly today."
                    })
                elif plant.water_needs == 'medium':
                    plant_recs.append({
                        "type": "watering",
                        "message": f"Moderate watering recommended for {plant.common_name}."
                    })
            
            # Add to recommendations if any were generated
            if plant_recs:
                recommendations.append({
                    "plant_id": plant.id,
                    "plant_name": plant.common_name,
                    "log_id": log.id,
                    "recommendations": plant_recs
                })
        
        return recommendations
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get aggregated data for the user's garden dashboard with weather insights"""
        user = request.user
        gardens = Garden.objects.filter(user=user, is_deleted=False)
        
        # Get total numbers
        garden_count = gardens.count()
        plant_count = GardenLog.objects.filter(garden__in=gardens).count()
        
        # Get upcoming tasks
        notifications = NotificationInstance.objects.filter(
            notification__garden__user=user,
            status='PENDING'
        ).order_by('next_due')[:5]
        
        # Prepare notification data for frontend
        upcoming_tasks = []
        for notification in notifications:
            upcoming_tasks.append({
                'id': notification.id,
                'name': notification.notification.name,
                'type': notification.notification.type,
                'garden_id': notification.notification.garden.id,
                'garden_name': notification.notification.garden.name,
                'due_date': notification.next_due,
                'is_overdue': notification.is_overdue
            })
        
        # Get plant health summary
        health_stats = GardenLog.objects.filter(garden__in=gardens).values(
            'health_status'
        ).annotate(count=Count('id'))
        
        health_summary = {}
        for stat in health_stats:
            health_summary[stat['health_status'] or 'Unknown'] = stat['count']
        
        # Get weather data if user has a zip code
        weather_insights = None
        if hasattr(user, 'profile') and user.profile.zip_code:
            try:
                weather_insights = get_garden_weather_insights(user.profile.zip_code)
                
                # Add summary of critical weather conditions
                critical_alerts = []
                
                if weather_insights['frost_warning']['frost_risk']:
                    critical_alerts.append({
                        'type': 'frost',
                        'message': f"Frost expected soon! Protect sensitive plants.",
                        'days': [day['date'] for day in weather_insights['frost_warning']['frost_days']]
                    })
                
                if weather_insights['extreme_heat_warning']['extreme_heat']:
                    critical_alerts.append({
                        'type': 'heat',
                        'message': "Extreme heat expected! Ensure plants are well-watered.",
                        'days': [day['date'] for day in weather_insights['extreme_heat_warning']['hot_days']]
                    })
                
                if weather_insights['high_wind_warning']['high_winds']:
                    critical_alerts.append({
                        'type': 'wind',
                        'message': "High winds expected! Check plant supports.",
                        'days': [day['date'] for day in weather_insights['high_wind_warning']['windy_days']]
                    })
                
                if weather_insights['watering_needed']['should_water']:
                    critical_alerts.append({
                        'type': 'water',
                        'message': weather_insights['watering_needed']['reason'],
                        'priority': 'high'
                    })
                
                # Add critical alerts to the weather insights
                weather_insights['critical_alerts'] = critical_alerts
            
            except WeatherServiceError:
                # If weather service fails, just continue without it
                weather_insights = None
            
        # Format response with optional weather data
        response_data = {
            'garden_count': garden_count,
            'plant_count': plant_count,
            'upcoming_tasks': upcoming_tasks,
            'health_summary': health_summary,
            'gardens': GardenSerializer(gardens, many=True).data
        }
        
        if weather_insights:
            response_data['weather'] = weather_insights
            
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def update_grid(self, request, pk=None):
        """Update the garden grid layout"""
        garden = self.get_object()
        cells_data = request.data.get('cells', [])
        
        # Validate grid dimensions
        if len(cells_data) != garden.size_y:
            return Response(
                {"error": "Grid height does not match garden size_y"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        for row in cells_data:
            if len(row) != garden.size_x:
                return Response(
                    {"error": "Grid width does not match garden size_x"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        garden.logs.all().delete()
        
        # Create new garden logs based on grid data
        for y, row in enumerate(cells_data):
            for x, cell in enumerate(row):
                if cell and 'id' in cell:  # Cell has a plant
                    GardenLog.objects.create(
                        garden=garden,
                        plant_id=cell['id'],
                        x_coordinate=x,
                        y_coordinate=y,
                        planted_date=timezone.now().date(),
                        health_status='Healthy'  # Default status
                    )
        
        # Return the updated garden grid
        serializer = GardenGridSerializer(garden)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get garden care recommendations based on weather and plants"""
        garden = self.get_object()
        
        # Get weather insights
        weather_insights = self._get_garden_weather_data(garden, request.user)
        if not weather_insights:
            return Response(
                {"detail": "Couldn't get weather data for this garden. Please check your location settings."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate garden-level recommendations
        recommendations = {
            "general": [],
            "plants": []
        }
        
        # Add general recommendations based on weather
        if weather_insights['watering_needed']['should_water']:
            recommendations["general"].append({
                "type": "watering",
                "priority": "high",
                "message": f"Water your garden today: {weather_insights['watering_needed']['reason']}"
            })
            
        if weather_insights['frost_warning']['frost_risk']:
            recommendations["general"].append({
                "type": "frost_protection",
                "priority": "high",
                "message": "Protect plants from frost in the next few days",
                "details": f"Temperatures as low as {weather_insights['frost_warning']['min_temperature']}°C expected"
            })
            
        if weather_insights['extreme_heat_warning']['extreme_heat']:
            recommendations["general"].append({
                "type": "heat_protection",
                "priority": "high",
                "message": "Protect plants from heat in the next few days",
                "details": f"Temperatures as high as {weather_insights['extreme_heat_warning']['max_temperature']}°C expected"
            })
            
        if weather_insights['high_wind_warning']['high_winds']:
            recommendations["general"].append({
                "type": "wind_protection",
                "priority": "medium",
                "message": "Secure tall plants and structures against wind",
                "details": f"Wind speeds up to {weather_insights['high_wind_warning']['max_wind_speed']} km/h expected"
            })
            
        # Get plant-specific recommendations
        recommendations["plants"] = self._generate_plant_weather_recommendations(garden, weather_insights)
        
        return Response(recommendations)


class GardenLogViewSet(viewsets.ModelViewSet):
    """API endpoint for Garden Logs (plants in a garden)"""
    serializer_class = GardenLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        """Return garden logs filtered by garden if specified"""
        queryset = GardenLog.objects.filter(garden__user=self.request.user)
        
        # Allow filtering by garden
        garden_id = self.request.query_params.get('garden', None)
        if garden_id:
            queryset = queryset.filter(garden_id=garden_id)
            
        return queryset
    
    def perform_create(self, serializer):
        """Create a new garden log entry (plant in garden)"""
        try:
            # Garden should already be validated by the serializer
            garden = serializer.validated_data.get('garden')
            
            # Extra verification that the garden belongs to the current user
            if garden.user != self.request.user:
                raise PermissionDenied("You don't have permission to add plants to this garden")
            
            # The serializer validation already checks for position conflicts,
            # but let's add a safety check here as well
            x_coordinate = serializer.validated_data.get('x_coordinate')
            y_coordinate = serializer.validated_data.get('y_coordinate')
            
            if GardenLog.objects.filter(
                garden=garden, 
                x_coordinate=x_coordinate, 
                y_coordinate=y_coordinate,
                is_deleted=False
            ).exists():
                raise ValidationError(
                    {"position": f"A plant already exists at position ({x_coordinate}, {y_coordinate})"}
                )
            
            # Save the garden log
            serializer.save()
            
        except Garden.DoesNotExist:
            raise ValidationError({"garden": "Garden does not exist"})
        except Exception as e:
            logger.error(f"Error creating garden log: {e}")
            raise APIException(f"Error creating garden log: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def update_health(self, request, pk=None):
        """Update the health status of a plant in the garden"""
        garden_log = self.get_object()
        health_status = request.data.get('health_status')
        
        if not health_status:
            return Response(
                {"error": "health_status field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        garden_log.health_status = health_status
        garden_log.save()
        
        return Response(GardenLogSerializer(garden_log).data)
    
    @action(detail=True, methods=['get'])
    def weather_compatibility(self, request, pk=None):
        """Check the compatibility of this plant with current weather conditions"""
        garden_log = self.get_object()
        garden = garden_log.garden
        plant = garden_log.plant
        
        # Get zip code from request params or user profile
        zip_code = request.query_params.get('zip_code')
        
        if not zip_code and hasattr(request.user, 'profile') and request.user.profile.zip_code:
            zip_code = request.user.profile.zip_code
        
        if not zip_code:
            return Response(
                {"detail": "No location information available. Please provide a zip_code parameter or update your profile."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            weather_insights = get_garden_weather_insights(zip_code)
            
            # Analyze compatibility
            compatibility = {
                "plant_id": plant.id,
                "plant_name": plant.common_name,
                "current_weather": weather_insights["current_weather"],
                "forecast_summary": weather_insights["forecast_summary"],
                "alerts": [],
                "care_tips": []
            }
            
            # Check for frost risk if plant has hardiness info
            if weather_insights['frost_warning']['frost_risk'] and hasattr(plant, 'frost_resistant'):
                if not plant.frost_resistant:
                    compatibility["alerts"].append({
                        "type": "frost",
                        "message": f"{plant.common_name} is sensitive to frost. Protect it during the upcoming cold temperatures."
                    })
                    compatibility["care_tips"].append("Consider covering plants with frost cloth or bringing potted plants indoors.")
            
            # Check for heat risk
            if weather_insights['extreme_heat_warning']['extreme_heat'] and hasattr(plant, 'heat_tolerant'):
                if not plant.heat_tolerant:
                    compatibility["alerts"].append({
                        "type": "heat",
                        "message": f"{plant.common_name} doesn't tolerate extreme heat well."
                    })
                    compatibility["care_tips"].append("Provide shade during the hottest part of the day and ensure consistent watering.")
            
            # Check watering needs
            if weather_insights['watering_needed']['should_water'] and hasattr(plant, 'water_needs'):
                if plant.water_needs == 'high':
                    compatibility["alerts"].append({
                        "type": "watering",
                        "message": f"{plant.common_name} has high water needs and conditions are dry."
                    })
                    compatibility["care_tips"].append("Water thoroughly, ensuring the soil is moist but not waterlogged.")
            
            return Response(compatibility)
            
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"detail": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )