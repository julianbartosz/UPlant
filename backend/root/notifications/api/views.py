# backend/root/notifications/api/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import logging

from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation
from notifications.api.serializers import (
    NotificationSerializer, NotificationInstanceSerializer,
    NotificationPlantAssociationSerializer, DashboardNotificationSerializer
)
from services.weather_service import get_garden_weather_insights, WeatherServiceError

# Set up logging
logger = logging.getLogger(__name__)

# Authentication class to handle CSRF exemption
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Do not enforce CSRF for API views
        return

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of a notification to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the notification owner
        return obj.garden.user == request.user

class NotificationViewSet(viewsets.ModelViewSet):
    """API endpoint for Notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'garden']
    search_fields = ['name', 'subtype']
    ordering_fields = ['created_at', 'name', 'type']
    ordering = ['type', 'name']
    
    def get_queryset(self):
        """Filter notifications to only show the user's notifications"""
        return Notification.objects.filter(garden__user=self.request.user)
    
    def perform_create(self, serializer):
        """Ensure new notifications are linked to the current user's garden"""
        garden = serializer.validated_data.get('garden')
        if garden.user != self.request.user:
            # Safety check, though serializer validation should catch this
            return Response(
                {"error": "You can only create notifications for your own gardens"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def add_plant(self, request, pk=None):
        """Add a plant to this notification"""
        notification = self.get_object()
        plant_id = request.data.get('plant_id')
        custom_interval = request.data.get('custom_interval')
        
        if not plant_id:
            return Response(
                {"error": "plant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if association already exists
            assoc, created = NotificationPlantAssociation.objects.get_or_create(
                notification=notification,
                plant_id=plant_id,
                defaults={'custom_interval': custom_interval}
            )
            
            if not created and custom_interval:
                # Update custom interval if provided
                assoc.custom_interval = custom_interval
                assoc.save()
                
            return Response({
                "success": True,
                "created": created,
                "association": NotificationPlantAssociationSerializer(assoc).data
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def remove_plant(self, request, pk=None):
        """Remove a plant from this notification"""
        notification = self.get_object()
        plant_id = request.data.get('plant_id')
        
        if not plant_id:
            return Response(
                {"error": "plant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            deleted, _ = NotificationPlantAssociation.objects.filter(
                notification=notification,
                plant_id=plant_id
            ).delete()
            
            return Response({
                "success": True,
                "deleted": deleted > 0
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get notification summary for user dashboard"""
        # Get user's upcoming notifications
        upcoming = NotificationInstance.objects.filter(
            notification__garden__user=request.user,
            status='PENDING'
        ).select_related('notification', 'notification__garden').order_by('next_due')
        
        # Group by notification
        notification_ids = upcoming.values_list('notification_id', flat=True).distinct()
        notifications = Notification.objects.filter(id__in=notification_ids)
        
        # Organize by time periods
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        overdue = []
        today_notifications = []
        tomorrow_notifications = []
        this_week_notifications = []
        later_notifications = []
        
        for notification in notifications:
            instance = notification.instances.filter(status='PENDING').order_by('next_due').first()
            if not instance:
                continue
                
            due_date = instance.next_due.date()
            
            # Add to appropriate list
            if instance.is_overdue:
                overdue.append(notification)
            elif due_date == today:
                today_notifications.append(notification)
            elif due_date == tomorrow:
                tomorrow_notifications.append(notification)
            elif due_date <= next_week:
                this_week_notifications.append(notification)
            else:
                later_notifications.append(notification)
        
        # Serialize the results
        serializer = DashboardNotificationSerializer
        
        # Get relevant weather alerts
        weather_alerts = self._get_weather_alerts(request.user)
        
        response_data = {
            'overdue': serializer(overdue, many=True).data,
            'today': serializer(today_notifications, many=True).data,
            'tomorrow': serializer(tomorrow_notifications, many=True).data,
            'this_week': serializer(this_week_notifications, many=True).data,
            'later': serializer(later_notifications, many=True).data,
        }
        
        # Add weather alerts if available
        if weather_alerts:
            response_data['weather_alerts'] = weather_alerts
            
        return Response(response_data)
    
    def _get_weather_alerts(self, user):
        """Get weather alerts for the user's location"""
        if not hasattr(user, 'profile') or not user.profile.zip_code:
            return None
            
        try:
            weather_data = get_garden_weather_insights(user.profile.zip_code)
            
            # Extract critical weather alerts
            alerts = []
            
            # Check for frost
            if weather_data['frost_warning']['frost_risk']:
                days = [day['date'] for day in weather_data['frost_warning']['frost_days']]
                alerts.append({
                    'type': 'frost',
                    'severity': 'high',
                    'title': 'Frost Warning',
                    'message': f"Protect your plants from frost expected on {', '.join(days)}.",
                    'affected_days': days
                })
            
            # Check for extreme heat
            if weather_data['extreme_heat_warning']['extreme_heat']:
                days = [day['date'] for day in weather_data['extreme_heat_warning']['hot_days']]
                alerts.append({
                    'type': 'heat',
                    'severity': 'high',
                    'title': 'Extreme Heat Warning',
                    'message': f"Protect plants from high temperatures on {', '.join(days)}.",
                    'affected_days': days
                })
            
            # Check for high winds
            if weather_data['high_wind_warning']['high_winds']:
                days = [day['date'] for day in weather_data['high_wind_warning']['windy_days']]
                alerts.append({
                    'type': 'wind',
                    'severity': 'medium',
                    'title': 'High Wind Warning',
                    'message': f"Secure plants and structures against strong winds on {', '.join(days)}.",
                    'affected_days': days
                })
            
            # Check for watering needs
            if weather_data['watering_needed']['should_water']:
                alerts.append({
                    'type': 'watering',
                    'severity': 'medium',
                    'title': 'Watering Recommended',
                    'message': weather_data['watering_needed']['reason'],
                    'days_since_rain': 'N/A'
                })
            
            return alerts if alerts else None
            
        except WeatherServiceError as e:
            logger.error(f"Error fetching weather alerts: {str(e)}")
            return None
    
    @action(detail=False, methods=['get'])
    def by_garden(self, request):
        """Get notifications organized by garden"""
        garden_id = request.query_params.get('garden_id')
        
        # If garden_id provided, filter by that garden
        queryset = self.get_queryset()
        if garden_id:
            queryset = queryset.filter(garden_id=garden_id)
        
        # Get notifications with upcoming instances
        result = {}
        
        for notification in queryset:
            garden_id = notification.garden_id
            
            if garden_id not in result:
                result[garden_id] = {
                    'garden_id': garden_id,
                    'garden_name': notification.garden.name or f"Garden {garden_id}",
                    'notifications': []
                }
            
            # Get next pending instance
            instance = notification.instances.filter(status='PENDING').order_by('next_due').first()
            if instance:
                notif_data = DashboardNotificationSerializer(notification).data
                result[garden_id]['notifications'].append(notif_data)
        
        # Convert to list
        return Response(list(result.values()))
    
    @action(detail=False, methods=['get'])
    def weather(self, request):
        """Get weather-based notifications for the user's gardens"""
        garden_id = request.query_params.get('garden_id')
        
        # Filter gardens
        if garden_id:
            gardens = request.user.gardens.filter(id=garden_id, is_deleted=False)
        else:
            gardens = request.user.gardens.filter(is_deleted=False)
            
        if not gardens.exists():
            return Response(
                {"detail": "No gardens found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get weather insights
        weather_notifications = []
        
        for garden in gardens:
            garden_data = {
                'garden_id': garden.id,
                'garden_name': garden.name or f"Garden {garden.id}",
                'alerts': []
            }
            
            # Try to get weather data
            try:
                if hasattr(request.user, 'profile') and request.user.profile.zip_code:
                    weather_data = get_garden_weather_insights(request.user.profile.zip_code)
                    
                    # Process weather insights into notifications
                    
                    # 1. Frost warnings
                    if weather_data['frost_warning']['frost_risk']:
                        frost_days = weather_data['frost_warning']['frost_days']
                        garden_data['alerts'].append({
                            'type': 'FROST',
                            'priority': 'high',
                            'title': 'Frost Alert',
                            'message': f"Protect sensitive plants from frost on {frost_days[0]['date']}",
                            'due_date': frost_days[0]['date'],
                            'temperature': frost_days[0]['temperature'],
                            'actions': ['Apply frost cloth', 'Move potted plants indoors', 'Water plants before frost']
                        })
                    
                    # 2. Extreme heat
                    if weather_data['extreme_heat_warning']['extreme_heat']:
                        hot_days = weather_data['extreme_heat_warning']['hot_days']
                        garden_data['alerts'].append({
                            'type': 'HEAT',
                            'priority': 'high',
                            'title': 'Heat Wave Alert',
                            'message': f"Protect plants from extreme heat on {hot_days[0]['date']}",
                            'due_date': hot_days[0]['date'],
                            'temperature': hot_days[0]['temperature'],
                            'actions': ['Water deeply in the morning', 'Provide shade', 'Mulch to retain moisture']
                        })
                    
                    # 3. High winds
                    if weather_data['high_wind_warning']['high_winds']:
                        windy_days = weather_data['high_wind_warning']['windy_days']
                        garden_data['alerts'].append({
                            'type': 'WIND',
                            'priority': 'medium',
                            'title': 'High Wind Alert',
                            'message': f"Secure plants against winds on {windy_days[0]['date']}",
                            'due_date': windy_days[0]['date'],
                            'wind_speed': windy_days[0]['wind_speed'],
                            'actions': ['Stake tall plants', 'Move potted plants to sheltered areas', 'Secure garden structures']
                        })
                    
                    # 4. Watering needs
                    if weather_data['watering_needed']['should_water']:
                        garden_data['alerts'].append({
                            'type': 'WATER',
                            'priority': 'medium',
                            'title': 'Watering Needed',
                            'message': weather_data['watering_needed']['reason'],
                            'due_date': timezone.now().date().isoformat(),
                            'next_rain': weather_data['watering_needed']['next_rain_forecast'],
                            'actions': ['Water deeply at soil level', 'Apply mulch to retain moisture']
                        })
                    
                    # Add garden data to results if it has alerts
                    if garden_data['alerts']:
                        weather_notifications.append(garden_data)
            
            except WeatherServiceError as e:
                logger.error(f"Weather service error for garden {garden.id}: {str(e)}")
        
        if not weather_notifications:
            return Response({"detail": "No weather alerts for your gardens at this time."})
            
        return Response(weather_notifications)
    
    @action(detail=False, methods=['post'])
    def create_weather_notifications(self, request):
        """Create actual notifications from weather alerts"""
        garden_id = request.data.get('garden_id')
        alert_type = request.data.get('alert_type')
        
        if not garden_id:
            return Response(
                {"error": "garden_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not alert_type or alert_type not in ['FROST', 'HEAT', 'WIND', 'WATER']:
            return Response(
                {"error": "Valid alert_type is required (FROST, HEAT, WIND, or WATER)"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            garden = request.user.gardens.get(id=garden_id, is_deleted=False)
        except Exception:
            return Response(
                {"error": "Garden not found or access denied"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Get weather data
        try:
            if not hasattr(request.user, 'profile') or not request.user.profile.zip_code:
                return Response(
                    {"error": "Please add a ZIP code to your profile settings."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            weather_data = get_garden_weather_insights(request.user.profile.zip_code)
            
            # Create appropriate notification based on type
            notification = None
            
            if alert_type == 'FROST' and weather_data['frost_warning']['frost_risk']:
                frost_day = weather_data['frost_warning']['frost_days'][0]['date']
                temp = weather_data['frost_warning']['frost_days'][0]['temperature']
                
                # Create or get frost warning notification
                notification, created = Notification.objects.get_or_create(
                    garden=garden,
                    type='WE',  # Weather type
                    subtype='FROST',
                    defaults={
                        'name': f"Frost Warning for {frost_day}",
                        'interval': 0  # One-time alert
                    }
                )
                
                if created or not notification.instances.filter(status='PENDING').exists():
                    # Create notification instance with the frost date as due date
                    from datetime import datetime
                    due_date = datetime.strptime(frost_day, '%Y-%m-%d')
                    
                    NotificationInstance.objects.create(
                        notification=notification,
                        next_due=due_date,
                        status='PENDING'
                    )
                    
            elif alert_type == 'HEAT' and weather_data['extreme_heat_warning']['extreme_heat']:
                hot_day = weather_data['extreme_heat_warning']['hot_days'][0]['date']
                temp = weather_data['extreme_heat_warning']['hot_days'][0]['temperature']
                
                notification, created = Notification.objects.get_or_create(
                    garden=garden,
                    type='WE',  # Weather type
                    subtype='HEAT',
                    defaults={
                        'name': f"Extreme Heat Warning for {hot_day}",
                        'interval': 0  # One-time alert
                    }
                )
                
                if created or not notification.instances.filter(status='PENDING').exists():
                    from datetime import datetime
                    due_date = datetime.strptime(hot_day, '%Y-%m-%d')
                    
                    NotificationInstance.objects.create(
                        notification=notification,
                        next_due=due_date,
                        status='PENDING'
                    )
                    
            elif alert_type == 'WIND' and weather_data['high_wind_warning']['high_winds']:
                windy_day = weather_data['high_wind_warning']['windy_days'][0]['date']
                wind_speed = weather_data['high_wind_warning']['windy_days'][0]['wind_speed']
                
                notification, created = Notification.objects.get_or_create(
                    garden=garden,
                    type='WE',  # Weather type
                    subtype='WIND',
                    defaults={
                        'name': f"High Wind Warning for {windy_day}",
                        'interval': 0  # One-time alert
                    }
                )
                
                if created or not notification.instances.filter(status='PENDING').exists():
                    from datetime import datetime
                    due_date = datetime.strptime(windy_day, '%Y-%m-%d')
                    
                    NotificationInstance.objects.create(
                        notification=notification,
                        next_due=due_date,
                        status='PENDING'
                    )
                    
            elif alert_type == 'WATER' and weather_data['watering_needed']['should_water']:
                notification, created = Notification.objects.get_or_create(
                    garden=garden,
                    type='WA',  # Watering type
                    subtype='WEATHER',
                    defaults={
                        'name': "Watering needed - Dry conditions",
                        'interval': 0  # One-time alert
                    }
                )
                
                if created or not notification.instances.filter(status='PENDING').exists():
                    # Create notification instance due today
                    NotificationInstance.objects.create(
                        notification=notification,
                        next_due=timezone.now(),
                        status='PENDING'
                    )
            
            if notification:
                return Response({
                    "success": True,
                    "notification": NotificationSerializer(notification).data
                })
            else:
                return Response(
                    {"error": f"No {alert_type} alert currently needed based on weather conditions"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except WeatherServiceError as e:
            logger.error(f"Weather service error: {str(e)}")
            return Response(
                {"error": "Unable to retrieve weather data. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error creating weather notification: {str(e)}")
            return Response(
                {"error": f"Failed to create notification: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationInstanceViewSet(viewsets.ModelViewSet):
    """API endpoint for NotificationInstances"""
    serializer_class = NotificationInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication, TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'notification']
    ordering_fields = ['next_due', 'status']
    ordering = ['next_due']
    
    def get_queryset(self):
        """Filter instances to only show the user's notification instances"""
        return NotificationInstance.objects.filter(
            notification__garden__user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark notification as completed"""
        instance = self.get_object()
        instance.complete_task()
        return Response({
            "success": True,
            "message": "Notification marked as completed",
            "instance": NotificationInstanceSerializer(instance).data
        })
    
    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Skip notification"""
        instance = self.get_object()
        instance.skip_task()
        return Response({
            "success": True,
            "message": "Notification skipped",
            "instance": NotificationInstanceSerializer(instance).data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_complete(self, request):
        """Complete multiple notification instances"""
        instance_ids = request.data.get('instance_ids', [])
        if not instance_ids:
            return Response(
                {"error": "instance_ids is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure user can only complete their own notifications
        instances = NotificationInstance.objects.filter(
            id__in=instance_ids,
            notification__garden__user=request.user
        )
        
        completed = 0
        for instance in instances:
            instance.complete_task()
            completed += 1
            
        return Response({
            "success": True,
            "completed": completed,
            "message": f"Completed {completed} notifications"
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming notifications for the user"""
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 7
            
        end_date = timezone.now() + timedelta(days=days)
        
        instances = self.get_queryset().filter(
            status='PENDING',
            next_due__lte=end_date
        ).order_by('next_due')
        
        return Response(NotificationInstanceSerializer(instances, many=True).data)