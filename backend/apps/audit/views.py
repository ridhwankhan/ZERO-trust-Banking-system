"""
Audit log views for admin access.
"""
from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.utils.dateparse import parse_datetime

from .models import AuditLog
from .permissions import CanViewAuditLogs


class AuditLogListView(generics.ListAPIView):
    """
    Admin view to list all audit logs.
    Only admins can access audit logs.
    """
    permission_classes = [CanViewAuditLogs]
    serializer_class = None  # Will define inline
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'action']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return audit logs with optional filtering."""
        queryset = AuditLog.objects.all().select_related('admin', 'target_user')
        
        # Filter by action type
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by admin
        admin_id = self.request.query_params.get('admin_id')
        if admin_id:
            queryset = queryset.filter(admin_id=admin_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            parsed_start = parse_datetime(start_date)
            if parsed_start:
                queryset = queryset.filter(created_at__gte=parsed_start)
        
        if end_date:
            parsed_end = parse_datetime(end_date)
            if parsed_end:
                queryset = queryset.filter(created_at__lte=parsed_end)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List audit logs with self-logging."""
        queryset = self.get_queryset()
        
        # Log that admin is viewing audit logs
        AuditLog.log_admin_action(
            admin=request.user,
            action=AuditLog.ACTION_VIEW_AUDIT_LOGS,
            details={
                'filters_applied': dict(request.query_params),
                'results_count': queryset.count()
            },
            request=request
        )
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = self._serialize_logs(page)
            return self.get_paginated_response(data)
        
        data = self._serialize_logs(queryset)
        return Response(data)
    
    def _serialize_logs(self, logs):
        """Serialize audit logs manually."""
        data = []
        for log in logs:
            log_data = {
                'id': log.id,
                'admin': {
                    'id': log.admin.id,
                    'email': log.admin.email,
                    'username': log.admin.username
                },
                'action': log.action,
                'action_display': log.get_action_display(),
                'target_user': {
                    'id': log.target_user.id,
                    'email': log.target_user.email,
                    'username': log.target_user.username
                } if log.target_user else None,
                'target_transaction_id': log.target_transaction_id,
                'details': log.details,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent[:100] + '...' if log.user_agent and len(log.user_agent) > 100 else log.user_agent,
                'created_at': log.created_at
            }
            data.append(log_data)
        return data


class AuditLogStatsView(APIView):
    """
    Admin view to get audit log statistics.
    """
    permission_classes = [CanViewAuditLogs]
    
    def get(self, request):
        """Get audit log statistics."""
        from django.db.models import Count
        
        # Get counts by action type
        action_counts = AuditLog.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Get counts by admin
        admin_counts = AuditLog.objects.values(
            'admin__id', 'admin__email', 'admin__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10
        
        # Get recent activity (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        last_24h = timezone.now() - timedelta(hours=24)
        recent_count = AuditLog.objects.filter(created_at__gte=last_24h).count()
        
        # Log this access
        AuditLog.log_admin_action(
            admin=request.user,
            action=AuditLog.ACTION_VIEW_AUDIT_LOGS,
            details={'stats_requested': True},
            request=request
        )
        
        return Response({
            'total_logs': AuditLog.objects.count(),
            'recent_24h': recent_count,
            'action_breakdown': list(action_counts),
            'top_admins': list(admin_counts),
            'timestamp': timezone.now()
        })
