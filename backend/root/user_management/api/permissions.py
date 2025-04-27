# backend/root/user_management/api/permissions.py

from rest_framework import permissions

class IsUserOrAdmin(permissions.BasePermission):
    """
    Permission to allow users to access only their own resources,
    or admins to access any resource.
    """
    
    def has_permission(self, request, view):
        # Allow authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.is_superuser:
            return True
            
        # Check if the object has a user attribute that matches the request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # If the object itself is a user, check if it's the request user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
            
        # Default deny
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to all users,
    but only allow write operations to admin users.
    """
    
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS to anyone
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for admin
        return request.user and request.user.is_superuser