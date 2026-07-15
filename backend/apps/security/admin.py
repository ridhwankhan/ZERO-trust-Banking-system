"""
Django Admin Registration for Security Models
"""

from django.contrib import admin
from .models import (
    LoginEvent, TrustedDevice,
    SecurityScanReport, LedgerIntegrityReport, SecurityAlert,
)


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'ip_address', 'browser', 'os',
        'country', 'risk_score', 'risk_level',
        'face_biometric_verified', 'is_successful', 'created_at',
    ]
    list_filter = ['risk_level', 'is_successful', 'face_biometric_verified', 'country']
    search_fields = ['user__email', 'ip_address', 'email_entered']
    readonly_fields = ['created_at']


@admin.register(TrustedDevice)
class TrustedDeviceAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'browser', 'os', 'trust_status',
        'has_face_biometric', 'last_used',
    ]
    list_filter = ['trust_status', 'has_face_biometric']
    search_fields = ['user__email', 'device_fingerprint']


@admin.register(SecurityScanReport)
class SecurityScanReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'scan_date', 'status', 'passed_tests_count', 'failed_tests_count']
    list_filter = ['status']


@admin.register(LedgerIntegrityReport)
class LedgerIntegrityReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'check_date', 'status', 'verified_count']
    list_filter = ['status']


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'alert_type', 'severity', 'user', 'is_resolved', 'created_at']
    list_filter = ['severity', 'is_resolved', 'alert_type']
    search_fields = ['message', 'user__email']
