"""
Security App URL Configuration
"""

import logging
from django.urls import path
from .views import (
    # Admin endpoints
    AdminSecurityDashboardView,
    AdminLoginHistoryView,
    AdminSecurityAlertsView,
    AdminResolveAlertView,
    AdminRunScanView,
    AdminScanHistoryView,
    AdminRunIntegrityCheckView,
    AdminIntegrityHistoryView,
    # User endpoints
    UserLoginHistoryView,
    UserTrustedDevicesView,
    UserRemoveDeviceView,
    UserSecurityAlertsView,
    UserReportNotMeView,
    # Adaptive Auth
    OTPRequestView,
    OTPVerifyView,
)

logger = logging.getLogger(__name__)

urlpatterns = [
    # ==================== ADMIN SECURITY DASHBOARD ====================
    path('admin/dashboard/', AdminSecurityDashboardView.as_view(), name='security-admin-dashboard'),
    path('admin/login-history/', AdminLoginHistoryView.as_view(), name='security-admin-login-history'),
    path('admin/alerts/', AdminSecurityAlertsView.as_view(), name='security-admin-alerts'),
    path('admin/alerts/<int:alert_id>/resolve/', AdminResolveAlertView.as_view(), name='security-admin-resolve-alert'),
    path('admin/scan/run/', AdminRunScanView.as_view(), name='security-admin-run-scan'),
    path('admin/scan/history/', AdminScanHistoryView.as_view(), name='security-admin-scan-history'),
    path('admin/integrity/run/', AdminRunIntegrityCheckView.as_view(), name='security-admin-run-integrity'),
    path('admin/integrity/history/', AdminIntegrityHistoryView.as_view(), name='security-admin-integrity-history'),

    # ==================== USER SECURITY CENTER ====================
    path('me/login-history/', UserLoginHistoryView.as_view(), name='security-user-login-history'),
    path('me/devices/', UserTrustedDevicesView.as_view(), name='security-user-devices'),
    path('me/devices/<int:device_id>/remove/', UserRemoveDeviceView.as_view(), name='security-user-remove-device'),
    path('me/alerts/', UserSecurityAlertsView.as_view(), name='security-user-alerts'),
    path('me/report-not-me/<int:login_id>/', UserReportNotMeView.as_view(), name='security-user-report-not-me'),

    # ==================== ADAPTIVE AUTH (OTP) ====================
    path('otp/request/', OTPRequestView.as_view(), name='security-otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='security-otp-verify'),
]

try:
    from . import webauthn_views
    urlpatterns += [
        path('webauthn/register/generate-options/', webauthn_views.WebAuthnRegisterOptionsView.as_view(), name='webauthn-register-options'),
        path('webauthn/register/verify/', webauthn_views.WebAuthnRegisterVerifyView.as_view(), name='webauthn-register-verify'),
        path('webauthn/authenticate/generate-options/', webauthn_views.WebAuthnAuthOptionsView.as_view(), name='webauthn-auth-options'),
        path('webauthn/authenticate/verify/', webauthn_views.WebAuthnAuthVerifyView.as_view(), name='webauthn-auth-verify'),
    ]
except Exception as exc:
    # Keep the rest of the security API up if the webauthn package failed to install
    logger.exception('WebAuthn routes disabled: %s', exc)
