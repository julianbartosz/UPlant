# backend/root/plants/api/views.py

import logging
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, viewsets, permissions, filters
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from plants.api.serializers import (
    PlantBaseSerializer, PlantDetailSerializer, UserPlantCreateSerializer, 
    UserPlantUpdateSerializer, AdminPlantSerializer, PlantChangeRequestSerializer,
    PlantChangeRequestCreateSerializer, TreflePlantSerializer, 
    TreflePlantListResponseSerializer
)
from services.trefle_service import list_plants, retrieve_plants
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
    GET /api/v1/trefle/plants
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
    GET /api/v1/trefle/plants/{id}
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
    
    list: GET /api/v1/plants/
    retrieve: GET /api/v1/plants/{id}/
    create: POST /api/v1/plants/ (admin only)
    update: PUT /api/v1/plants/{id}/ (admin only)
    partial_update: PATCH /api/v1/plants/{id}/ (admin only)
    destroy: DELETE /api/v1/plants/{id}/ (admin only)
    
    Additional actions:
    - create_user_plant: POST /api/v1/plants/create-custom/
    - user_update: PATCH /api/v1/plants/{id}/user-update/
    - user_plants: GET /api/v1/plants/user-plants/
    - submit_change: POST /api/v1/plants/{id}/submit-change/
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
        elif self.action in ['create_user_plant', 'user_plants', 'submit_change']:
            # Any authenticated user can create their own plants
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

class PlantChangeRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing plant change requests.
    
    list: GET /api/v1/changes/
    retrieve: GET /api/v1/changes/{id}/
    create: POST /api/v1/changes/ 
    update: PUT /api/v1/changes/{id}/ (admin only)
    partial_update: PATCH /api/v1/changes/{id}/ (admin only)
    destroy: DELETE /api/v1/changes/{id}/ (admin only)
    
    Additional actions:
    - approve: POST /api/v1/changes/{id}/approve/
    - reject: POST /api/v1/changes/{id}/reject/
    - user_changes: GET /api/v1/changes/user-changes/
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
    GET /api/v1/plants/statistics
    Provides statistics about plants in the system.
    """
    permission_classes = [permissions.IsAuthenticated]
    
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