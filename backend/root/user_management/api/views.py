# backend/root/user_management/api/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification, NotificationInstance
from .serializers import NotificationSerializer, NotificationInstanceSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Only return notifications for gardens the user has access to"""
        user = self.request.user
        return Notification.objects.filter(garden__user=user)
    
    @action(detail=True, methods=['post'])
    def create_instance(self, request, pk=None):
        """Manually create a new instance for a notification"""
        notification = self.get_object()
        instance = NotificationInstance.objects.create(
            notification=notification,
            next_due=timezone.now() + timedelta(days=notification.interval)
        )
        serializer = NotificationInstanceSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class NotificationInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationInstanceSerializer
    
    def get_queryset(self):
        """Return notification instances for the current user"""
        user = self.request.user
        return NotificationInstance.objects.filter(
            notification__garden__user=user
        ).order_by('next_due')
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a notification instance as completed"""
        instance = self.get_object()
        instance.complete_task()
        serializer = NotificationInstanceSerializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Skip a notification instance"""
        instance = self.get_object()
        instance.skip_task()
        serializer = NotificationInstanceSerializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get all notifications due today"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            next_due__date=today, 
            status='PENDING'
        )
        serializer = NotificationInstanceSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue notifications"""
        now = timezone.now()
        queryset = self.get_queryset().filter(
            next_due__lt=now, 
            status='PENDING'
        )
        serializer = NotificationInstanceSerializer(queryset, many=True)
        return Response(serializer.data)