from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission to only allow admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsUser(permissions.BasePermission):
    """Permission to only allow regular users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_user


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to only allow owners of an object or admins."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.id == request.user.id


class CanCreateTransaction(permissions.BasePermission):
    """Permission to create transactions (all authenticated users)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanViewAllTransactions(permissions.BasePermission):
    """Permission to view all transactions (admin only)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class CanManageUsers(permissions.BasePermission):
    """Permission to manage users (admin only)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class CanViewAuditLogs(permissions.BasePermission):
    """Permission to view audit logs (admin only)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class CanSendMoney(permissions.BasePermission):
    """Permission to send money (all authenticated users with balance check)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
