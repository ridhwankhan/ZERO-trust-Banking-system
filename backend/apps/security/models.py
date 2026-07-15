"""
Zero Trust Security Models
==========================
Models for behavioral threat detection, device trust management,
security scan reports, ledger integrity checks, and security alerts.
Face biometric recognition is supported as an optional verification method.
"""

from django.db import models
from apps.users.models import User


# ============================================================
# MODULE 1: Behavioral Threat Detection
# ============================================================

class LoginEvent(models.Model):
    """
    Records every login attempt (successful or failed) with full device,
    network, and biometric context for risk scoring.
    """
    RISK_LEVEL_LOW = 'low'
    RISK_LEVEL_MEDIUM = 'medium'
    RISK_LEVEL_HIGH = 'high'
    RISK_LEVEL_CHOICES = [
        (RISK_LEVEL_LOW, 'Low'),
        (RISK_LEVEL_MEDIUM, 'Medium'),
        (RISK_LEVEL_HIGH, 'High'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, related_name='login_events',
        help_text="NULL when the login email doesn't match any user"
    )
    email_entered = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Email that was typed into the login form"
    )

    # Network & Device info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    browser = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    device_fingerprint = models.CharField(max_length=255, null=True, blank=True)

    # Biometric Face Recognition Support (optional)
    face_biometric_verified = models.BooleanField(
        default=False,
        help_text="True if user passed face recognition during this login"
    )
    face_signature_hash = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Hash of the face scan data submitted with this login"
    )

    # Geolocation
    country = models.CharField(max_length=100, default='Unknown')
    city = models.CharField(max_length=100, default='Unknown')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Risk evaluation
    risk_score = models.IntegerField(default=0)
    risk_level = models.CharField(
        max_length=10, choices=RISK_LEVEL_CHOICES, default=RISK_LEVEL_LOW
    )
    risk_reasons = models.JSONField(
        default=list, blank=True,
        help_text="List of reasons that contributed to the risk score"
    )
    impossible_travel_detected = models.BooleanField(default=False)

    # Outcome
    is_successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
            models.Index(fields=['risk_level', '-created_at']),
        ]

    def __str__(self):
        email = self.user.email if self.user else self.email_entered
        status = "OK" if self.is_successful else "FAIL"
        return f"{email} | {self.ip_address} | {status} | risk={self.risk_level}"


class TrustedDevice(models.Model):
    """
    A recognized device that the user has previously logged in from.
    Optionally stores a face biometric hash for this device.
    """
    STATUS_TRUSTED = 'trusted'
    STATUS_REMOVED = 'removed'
    STATUS_CHOICES = [
        (STATUS_TRUSTED, 'Trusted'),
        (STATUS_REMOVED, 'Removed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='trusted_devices'
    )
    device_fingerprint = models.CharField(max_length=255)
    browser = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=255, default='Recognized Device')

    # Biometric Face Recognition Support (optional)
    has_face_biometric = models.BooleanField(
        default=False,
        help_text="True if user enrolled face biometric on this device"
    )
    face_signature_hash = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Hash of the enrolled face template"
    )

    trust_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_TRUSTED
    )
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trusted_devices'
        unique_together = ('user', 'device_fingerprint')

    def __str__(self):
        bio = " [Face]" if self.has_face_biometric else ""
        return f"{self.user.email} - {self.browser}/{self.os}{bio}"


# ============================================================
# MODULE 2: Security & Regression Scanner
# ============================================================

class SecurityScanReport(models.Model):
    """
    Results of an internal OWASP-style security regression scan.
    Each row is one full scan run containing multiple test results.
    """
    STATUS_PASS = 'pass'
    STATUS_FAIL = 'fail'
    STATUS_CHOICES = [
        (STATUS_PASS, 'Pass'),
        (STATUS_FAIL, 'Fail'),
    ]

    scan_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PASS)
    passed_tests_count = models.IntegerField(default=0)
    failed_tests_count = models.IntegerField(default=0)
    details = models.JSONField(
        default=list, blank=True,
        help_text="Array of {test_name, status, severity, recommendation}"
    )

    class Meta:
        db_table = 'security_scan_reports'
        ordering = ['-scan_date']

    def __str__(self):
        return f"Scan {self.scan_date:%Y-%m-%d %H:%M} - {self.status.upper()}"


# ============================================================
# MODULE 3: Cryptographic Ledger Integrity
# ============================================================

class LedgerIntegrityReport(models.Model):
    """
    Results of the background integrity verification daemon.
    Records how many transactions were verified and any tampered records.
    """
    STATUS_SECURE = 'secure'
    STATUS_TAMPERED = 'tampered'
    STATUS_CHOICES = [
        (STATUS_SECURE, 'Secure'),
        (STATUS_TAMPERED, 'Tampered'),
    ]

    check_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SECURE)
    verified_count = models.IntegerField(default=0)
    tampered_details = models.JSONField(
        default=list, blank=True,
        help_text="Array of {transaction_id, expected_hash, actual_hash}"
    )

    class Meta:
        db_table = 'ledger_integrity_reports'
        ordering = ['-check_date']

    def __str__(self):
        return f"Integrity {self.check_date:%Y-%m-%d %H:%M} - {self.status.upper()}"


# ============================================================
# Shared: Security Alerts / Notifications
# ============================================================

class SecurityAlert(models.Model):
    """
    Centralized alerts for all security modules.
    Used by admin dashboard and user security center.
    """
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, related_name='security_alerts'
    )
    alert_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_LOW)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'security_alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.alert_type} - {self.created_at:%H:%M}"
