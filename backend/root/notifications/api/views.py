# backend/root/notifications/api/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation
from notifications.api.serializers import (
    NotificationSerializer, NotificationInstanceSerializer,
    NotificationPlantAssociationSerializer, DashboardNotificationSerializer
)

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
        
        return Response({
            'overdue': serializer(overdue, many=True).data,
            'today': serializer(today_notifications, many=True).data,
            'tomorrow': serializer(tomorrow_notifications, many=True).data,
            'this_week': serializer(this_week_notifications, many=True).data,
            'later': serializer(later_notifications, many=True).data
        })
    
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


class NotificationInstanceViewSet(viewsets.ModelViewSet):
    """API endpoint for NotificationInstances"""
    serializer_class = NotificationInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]
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