"""
RBAC Permission classes for transactions.
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsTransactionParticipantOrAdmin(permissions.BasePermission):
    """
    Permission to only allow:
    - Sender or receiver of the transaction
    - Admin users (with restrictions)
    
    Admins can view transactions but cannot see encrypted payloads
    for HIGH_PRIVACY transactions.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Owner can always access
        if user == obj.sender or user == obj.receiver:
            return True
        
        # Admin can view but with restrictions (handled in view)
        if user.is_admin:
            return True
        
        return False


class CanViewLedger(permissions.BasePermission):
    """
    Permission to view ledger:
    - Users can view their own ledger
    - Admins can view any ledger (with audit log)
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # User can view own ledger
        if user == obj.user:
            return True
        
        # Admin can view any ledger
        if user.is_admin:
            return True
        
        return False


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
