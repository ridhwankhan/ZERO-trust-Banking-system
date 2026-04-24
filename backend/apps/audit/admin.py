from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'admin', 'action', 'target_user', 
        'target_transaction_id', 'ip_address', 'created_at'
    ]
    list_filter = ['action', 'created_at']
    search_fields = [
        'admin__email', 'admin__username',
        'target_user__email', 'target_user__username'
    ]
    readonly_fields = [
        'admin', 'action', 'target_user', 'target_transaction_id',
        'details', 'ip_address', 'user_agent', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        # Audit logs should only be created programmatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs should not be modified
        return False
