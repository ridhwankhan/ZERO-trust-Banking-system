"""
RBAC Permission classes for audit logs.
"""
from rest_framework import permissions


class CanViewAuditLogs(permissions.BasePermission):
    """
    Permission to view audit logs.
    Only admins can view audit logs.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )
