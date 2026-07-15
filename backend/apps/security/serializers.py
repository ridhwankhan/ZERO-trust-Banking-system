"""
Security REST API Serializers
"""

from rest_framework import serializers
from .models import LoginEvent, TrustedDevice, SecurityScanReport, LedgerIntegrityReport, SecurityAlert


class LoginEventSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, default='Unknown')

    class Meta:
        model = LoginEvent
        fields = [
            'id', 'user_email', 'email_entered', 'ip_address', 'user_agent',
            'browser', 'os', 'device_fingerprint',
            'face_biometric_verified', 'face_signature_hash',
            'country', 'city', 'latitude', 'longitude',
            'risk_score', 'risk_level', 'risk_reasons',
            'impossible_travel_detected', 'is_successful', 'created_at',
        ]


class TrustedDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustedDevice
        fields = [
            'id', 'device_fingerprint', 'browser', 'os', 'name',
            'has_face_biometric', 'face_signature_hash',
            'trust_status', 'last_used', 'created_at',
        ]


class SecurityScanReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityScanReport
        fields = [
            'id', 'scan_date', 'status',
            'passed_tests_count', 'failed_tests_count', 'details',
        ]


class LedgerIntegrityReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerIntegrityReport
        fields = [
            'id', 'check_date', 'status',
            'verified_count', 'tampered_details',
        ]


class SecurityAlertSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)

    class Meta:
        model = SecurityAlert
        fields = [
            'id', 'user_email', 'alert_type', 'severity',
            'message', 'is_resolved', 'created_at',
        ]
