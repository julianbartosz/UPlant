# backend/root/gardens/api/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from gardens.models import Garden, GardenLog
from gardens.api.serializers import GardenSerializer, GardenLogSerializer, GardenGridSerializer
from notifications.models import NotificationInstance
from django.db.models import Count, Q
from django.utils import timezone
import logging

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
    
    @action(detail=True, methods=['get'])
    def grid(self, request, pk=None):
        """Return the garden in grid format for the frontend"""
        garden = self.get_object()
        serializer = GardenGridSerializer(garden)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get aggregated data for the user's garden dashboard"""
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
            
        # Format response 
        return Response({
            'garden_count': garden_count,
            'plant_count': plant_count,
            'upcoming_tasks': upcoming_tasks,
            'health_summary': health_summary,
            'gardens': GardenSerializer(gardens, many=True).data
        })
    
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
        """Ensure the garden belongs to the current user"""
        garden_id = self.request.data.get('garden')
        garden = Garden.objects.get(id=garden_id, user=self.request.user)
        serializer.save(garden=garden)
    
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