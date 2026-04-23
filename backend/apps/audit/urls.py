from django.urls import path
from .views import AuditLogListView, AuditLogStatsView

urlpatterns = [
    path('logs/', AuditLogListView.as_view(), name='audit-logs-list'),
    path('stats/', AuditLogStatsView.as_view(), name='audit-logs-stats'),
]
