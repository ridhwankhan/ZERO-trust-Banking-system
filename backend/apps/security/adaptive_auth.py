"""
Adaptive Authentication Service (Module 4)
==========================================
Decides what verification level is required for a given action
based on the user's current risk level.

Also provides email notification helpers for security events.
"""

import random
import string
import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import SecurityAlert

logger = logging.getLogger(__name__)


# ============================================================
# OTP Generation / Verification (simple in-memory store)
# ============================================================

# In-memory OTP store: { user_id: {'code': '123456', 'purpose': 'login'} }
_otp_store = {}


def generate_otp(user, purpose='login'):
    """Generate a 6-digit OTP and store it. Returns the code string."""
    code = ''.join(random.choices(string.digits, k=6))
    _otp_store[user.id] = {
        'code': code,
        'purpose': purpose,
    }
    logger.info("OTP generated for user %s (purpose=%s)", user.email, purpose)
    return code


def verify_otp(user, code, purpose='login'):
    """Return True if the code matches the stored OTP for this purpose."""
    stored = _otp_store.get(user.id)
    if not stored:
        return False
    if stored['code'] == code and stored['purpose'] == purpose:
        # Consume the OTP
        del _otp_store[user.id]
        return True
    return False


# ============================================================
# Adaptive challenge decision
# ============================================================

def get_required_verification(risk_level, action='login'):
    """
    Based on risk_level ('low' / 'medium' / 'high') and the action,
    return a dict describing what extra verification is needed.

    Returns:
        {
            'requires_otp': bool,
            'requires_email_verification': bool,
            'restrict_sensitive_ops': bool,
            'message': str,
        }
    """
    if risk_level == 'high':
        return {
            'requires_otp': True,
            'requires_email_verification': True,
            'restrict_sensitive_ops': True,
            'message': (
                'High-risk activity detected. OTP and email verification '
                'required. Sensitive operations are temporarily restricted.'
            ),
        }
    elif risk_level == 'medium':
        return {
            'requires_otp': True,
            'requires_email_verification': False,
            'restrict_sensitive_ops': False,
            'message': 'Medium-risk activity detected. OTP verification required.',
        }
    else:
        return {
            'requires_otp': False,
            'requires_email_verification': False,
            'restrict_sensitive_ops': False,
            'message': 'Low risk. Normal authentication sufficient.',
        }


def is_sensitive_operation(action_name):
    """Return True if the action requires extra verification when risk > low."""
    sensitive = {
        'transfer', 'send_money', 'change_password',
        'change_email', 'update_profile', 'large_transaction',
    }
    return action_name in sensitive


# ============================================================
# Email notification helpers
# ============================================================

def send_security_email(user, subject, message):
    """Send a security notification email (uses console backend in dev)."""
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'security@zerotrust-bank.com')
    try:
        send_mail(
            subject=f"[SecureBank] {subject}",
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Security email sent to %s: %s", user.email, subject)
    except Exception as exc:
        logger.error("Failed to send security email to %s: %s", user.email, exc)


def notify_new_device_login(user, device_info):
    """Notify user of a login from an unrecognised device."""
    send_security_email(
        user,
        "New Device Login Detected",
        (
            f"Hello {user.username},\n\n"
            f"A login to your account was detected from a new device:\n"
            f"  Browser : {device_info.get('browser', 'Unknown')}\n"
            f"  OS      : {device_info.get('os', 'Unknown')}\n"
            f"  IP      : {device_info.get('ip', 'Unknown')}\n"
            f"  Location: {device_info.get('city', '?')}, "
            f"{device_info.get('country', '?')}\n\n"
            f"If this wasn't you, please visit your Security Center "
            f"immediately and revoke this device.\n"
        ),
    )


def notify_high_risk_login(user, risk_score, reasons):
    """Notify user of a high-risk login attempt."""
    send_security_email(
        user,
        "High-Risk Login Alert",
        (
            f"Hello {user.username},\n\n"
            f"A high-risk login attempt was detected on your account.\n"
            f"  Risk Score: {risk_score}/100\n"
            f"  Reasons:\n"
            + '\n'.join(f"    - {r}" for r in reasons) +
            f"\n\nYour account may be temporarily restricted. "
            f"Please verify your identity.\n"
        ),
    )


def notify_suspicious_transaction(user, amount, reasons):
    """Notify user of a suspicious financial transaction."""
    send_security_email(
        user,
        "Suspicious Transaction Alert",
        (
            f"Hello {user.username},\n\n"
            f"A transaction of {amount} was flagged as suspicious:\n"
            + '\n'.join(f"  - {r}" for r in reasons) +
            f"\n\nIf you did not initiate this transaction, "
            f"contact support immediately.\n"
        ),
    )
