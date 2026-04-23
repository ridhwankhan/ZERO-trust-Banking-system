from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission to only allow admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to only allow owners of an object or admins."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.id == request.user.id
