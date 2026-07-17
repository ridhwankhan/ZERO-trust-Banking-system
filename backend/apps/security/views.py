"""
Security REST API Views
=======================
Endpoints for admin dashboards, user security centers, scan triggers,
integrity checks, OTP verification, and device management.
"""

import logging

from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q

from .models import (
    LoginEvent, TrustedDevice,
    SecurityScanReport, LedgerIntegrityReport, SecurityAlert,
)
from .serializers import (
    LoginEventSerializer, TrustedDeviceSerializer,
    SecurityScanReportSerializer, LedgerIntegrityReportSerializer,
    SecurityAlertSerializer,
)
from .scanner_service import run_security_scan
from .integrity_checker import verify_ledger_integrity
from .adaptive_auth import generate_otp, verify_otp, send_security_email

logger = logging.getLogger(__name__)


# ============================================================
# Permission helpers
# ============================================================

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


# ============================================================
# ADMIN: Unified Security Dashboard
# ============================================================

class AdminSecurityDashboardView(APIView):
    """Single endpoint returning aggregated security stats for the admin."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        recent_logins = LoginEvent.objects.all()[:20]
        high_risk_users = (
            LoginEvent.objects
            .filter(risk_level='high', is_successful=True)
            .values('user__email')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        failed_logins = LoginEvent.objects.filter(is_successful=False).count()
        alerts = SecurityAlert.objects.filter(is_resolved=False)[:20]
        latest_scan = SecurityScanReport.objects.first()
        latest_integrity = LedgerIntegrityReport.objects.first()
        device_stats = {
            'total_devices': TrustedDevice.objects.filter(trust_status='trusted').count(),
            'removed_devices': TrustedDevice.objects.filter(trust_status='removed').count(),
        }
        auth_stats = {
            'total_logins': LoginEvent.objects.count(),
            'successful_logins': LoginEvent.objects.filter(is_successful=True).count(),
            'failed_logins': failed_logins,
            'face_biometric_logins': LoginEvent.objects.filter(face_biometric_verified=True).count(),
            'impossible_travel_events': LoginEvent.objects.filter(impossible_travel_detected=True).count(),
        }

        return Response({
            'recent_logins': LoginEventSerializer(recent_logins, many=True).data,
            'high_risk_users': list(high_risk_users),
            'alerts': SecurityAlertSerializer(alerts, many=True).data,
            'latest_scan': SecurityScanReportSerializer(latest_scan).data if latest_scan else None,
            'latest_integrity': LedgerIntegrityReportSerializer(latest_integrity).data if latest_integrity else None,
            'device_stats': device_stats,
            'auth_stats': auth_stats,
        })


# ============================================================
# ADMIN: Login History
# ============================================================

class AdminLoginHistoryView(generics.ListAPIView):
    """Paginated login event history for admin review."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = LoginEventSerializer
    queryset = LoginEvent.objects.all()


# ============================================================
# ADMIN: Security Alerts
# ============================================================

class AdminSecurityAlertsView(generics.ListAPIView):
    """All security alerts for admin review."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = SecurityAlertSerializer
    queryset = SecurityAlert.objects.all()


class AdminResolveAlertView(APIView):
    """Mark a security alert as resolved."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, alert_id):
        try:
            alert = SecurityAlert.objects.get(id=alert_id)
            alert.is_resolved = True
            alert.save()
            return Response({'message': 'Alert resolved'})
        except SecurityAlert.DoesNotExist:
            return Response({'error': 'Alert not found'}, status=404)


# ============================================================
# ADMIN: Trigger Security Scan
# ============================================================

class AdminRunScanView(APIView):
    """Trigger an internal OWASP security regression scan."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        report = run_security_scan()
        return Response(
            SecurityScanReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class AdminScanHistoryView(generics.ListAPIView):
    """List past security scan reports."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = SecurityScanReportSerializer
    queryset = SecurityScanReport.objects.all()


# ============================================================
# ADMIN: Trigger Integrity Check
# ============================================================

class AdminRunIntegrityCheckView(APIView):
    """Trigger a full ledger integrity verification."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        report = verify_ledger_integrity()
        return Response(
            LedgerIntegrityReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class AdminIntegrityHistoryView(generics.ListAPIView):
    """List past integrity check reports."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = LedgerIntegrityReportSerializer
    queryset = LedgerIntegrityReport.objects.all()


# ============================================================
# USER: Security Center
# ============================================================

class UserLoginHistoryView(generics.ListAPIView):
    """User's own login history."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoginEventSerializer

    def get_queryset(self):
        return LoginEvent.objects.filter(user=self.request.user)


class UserTrustedDevicesView(generics.ListAPIView):
    """User's trusted devices."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrustedDeviceSerializer

    def get_queryset(self):
        return TrustedDevice.objects.filter(
            user=self.request.user,
            trust_status=TrustedDevice.STATUS_TRUSTED,
        )


class UserRemoveDeviceView(APIView):
    """Revoke a trusted device — blocks future API access from that fingerprint."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, device_id):
        from .models import SecurityAlert

        try:
            device = TrustedDevice.objects.get(id=device_id, user=request.user)
        except TrustedDevice.DoesNotExist:
            return Response({'error': 'Device not found'}, status=404)

        if device.trust_status == TrustedDevice.STATUS_REMOVED:
            return Response({'message': 'Device already revoked', 'revoked': True})

        device.trust_status = TrustedDevice.STATUS_REMOVED
        device.has_face_biometric = False
        device.face_signature_hash = None
        device.save(update_fields=[
            'trust_status', 'has_face_biometric', 'face_signature_hash', 'last_used'
        ])

        SecurityAlert.objects.create(
            user=request.user,
            alert_type='device_revoked',
            severity=SecurityAlert.SEVERITY_MEDIUM,
            message=(
                f'Revoked trusted device "{device.name}" ({device.browser} / {device.os}). '
                f'Active sessions on that device are now blocked.'
            ),
        )

        current_fp = request.META.get('HTTP_X_DEVICE_FINGERPRINT', '')
        revoked_current = current_fp and current_fp == device.device_fingerprint

        return Response({
            'message': 'Device revoked. Sessions on that device are now blocked.',
            'revoked': True,
            'revoked_current_device': revoked_current,
            'device_id': device.id,
        })


class UserSecurityAlertsView(generics.ListAPIView):
    """User's own security alerts / notifications."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SecurityAlertSerializer

    def get_queryset(self):
        return SecurityAlert.objects.filter(user=self.request.user)


class UserReportNotMeView(APIView):
    """User reports 'This wasn't me' for a login event."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, login_id):
        try:
            event = LoginEvent.objects.get(id=login_id, user=request.user)
            SecurityAlert.objects.create(
                user=request.user,
                alert_type='USER_REPORT_NOT_ME',
                severity=SecurityAlert.SEVERITY_HIGH,
                message=(
                    f"User {request.user.email} reported login #{event.id} "
                    f"(IP: {event.ip_address}, {event.browser}/{event.os}) "
                    f"as suspicious."
                ),
            )
            return Response({'message': 'Report submitted. Our team will review it.'})
        except LoginEvent.DoesNotExist:
            return Response({'error': 'Login event not found'}, status=404)


# ============================================================
# OTP Verification endpoint (Adaptive Auth – Module 4)
# ============================================================

class OTPRequestView(APIView):
    """Generate and send an OTP to the authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        purpose = request.data.get('purpose', 'login')
        code = generate_otp(request.user, purpose=purpose)
        send_security_email(
            request.user,
            "Your Verification Code",
            f"Your one-time verification code is: {code}\n\n"
            f"This code is valid for a single use.",
        )
        return Response({'message': 'OTP sent to your email'})


class OTPVerifyView(APIView):
    """Verify an OTP code for adaptive auth challenges."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '')
        purpose = request.data.get('purpose', 'login')
        if verify_otp(request.user, code, purpose=purpose):
            return Response({'verified': True, 'message': 'OTP verified successfully'})
        return Response(
            {'verified': False, 'error': 'Invalid or expired OTP'},
            status=status.HTTP_400_BAD_REQUEST,
        )
