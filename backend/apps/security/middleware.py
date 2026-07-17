"""
Security Protection Middleware (Module 2 – active layer)
========================================================
Inspects every incoming request for SQL-injection, XSS, and
RBAC violations.  Blocked requests are logged as SecurityAlerts.
"""

import re
import json
import logging

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Pre-compiled patterns for speed
_SQLI_PATTERNS = [
    re.compile(r"'\s*(or|and)\s+.*=.*", re.IGNORECASE),
    re.compile(r"union\s+(all\s+)?select", re.IGNORECASE),
    re.compile(r"--\s*;?", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"drop\s+table", re.IGNORECASE),
]

_XSS_PATTERNS = [
    re.compile(r"<script.*?>.*?</script.*?>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on(load|error|click|mouseover)\s*=", re.IGNORECASE),
    re.compile(r"<iframe.*?>", re.IGNORECASE),
]


class SecurityProtectionMiddleware(MiddlewareMixin):
    """
    Zero Trust Active Protection – runs after AuthenticationMiddleware so
    that ``request.user`` is available for RBAC checks.
    """

    # -----------------------------------------------------------------
    # Public entry point called by Django on every request
    # -----------------------------------------------------------------
    def process_request(self, request):
        # 1. Check query-string parameters
        for key, value in request.GET.items():
            if self._is_malicious(value):
                return self._block(
                    request,
                    "SQLi/XSS in Query String",
                    f"param {key}",
                )

        # 2. Check JSON body on mutating verbs
        if request.method in ('POST', 'PUT', 'PATCH'):
            ct = getattr(request, 'content_type', '') or ''
            if 'application/json' in ct:
                try:
                    body = request.body.decode('utf-8', errors='replace')
                    if body and self._is_malicious(body):
                        return self._block(
                            request,
                            "SQLi/XSS in JSON Body",
                            "Malicious payload detected",
                        )
                except Exception as exc:
                    logger.error("Body inspection error: %s", exc)

        # 3. RBAC – non-admin hitting admin-only endpoints
        path = request.path
        if '/api/transactions/admin/' in path or '/api/audit/' in path:
            user = getattr(request, 'user', None)
            if user and user.is_authenticated and user.role != 'admin':
                return self._block(
                    request,
                    "RBAC Authorization Violation",
                    f"User {user.email} tried admin path {path}",
                )

        # 4. Block API access from devices the user explicitly revoked
        if path.startswith('/api/') and not path.startswith('/api/auth/'):
            user = getattr(request, 'user', None)
            fp = request.META.get('HTTP_X_DEVICE_FINGERPRINT', '')
            if user and user.is_authenticated and fp:
                from .models import TrustedDevice
                if TrustedDevice.objects.filter(
                    user=user,
                    device_fingerprint=fp,
                    trust_status=TrustedDevice.STATUS_REMOVED,
                ).exists():
                    return JsonResponse(
                        {
                            'error': (
                                'This device was removed from your account. '
                                'Sign in again from a trusted device.'
                            ),
                            'code': 'device_revoked',
                        },
                        status=403,
                    )

        return None  # Allow the request

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------
    @staticmethod
    def _is_malicious(text):
        for p in _SQLI_PATTERNS:
            if p.search(text):
                return True
        for p in _XSS_PATTERNS:
            if p.search(text):
                return True
        return False

    @staticmethod
    def _block(request, threat_type, detail):
        # Lazy import to avoid circular imports at module load
        from .models import SecurityAlert

        user = (
            request.user
            if hasattr(request, 'user') and request.user.is_authenticated
            else None
        )
        SecurityAlert.objects.create(
            user=user,
            alert_type=threat_type,
            severity=SecurityAlert.SEVERITY_HIGH,
            message=(
                f"Blocked by middleware. "
                f"IP={request.META.get('REMOTE_ADDR')}. {detail}"
            ),
        )
        logger.warning("BLOCKED %s – %s – %s", threat_type, detail,
                        request.META.get('REMOTE_ADDR'))
        return JsonResponse(
            {
                'status': 'blocked',
                'error': 'Security Protection triggered',
                'threat': threat_type,
                'details': 'Malicious payload rejected by zero-trust gateway.',
            },
            status=400,
        )
