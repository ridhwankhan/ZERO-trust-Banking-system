"""
Behavioral Risk Engine (Module 1)
=================================
Evaluates login risk and transaction risk using device fingerprints,
geolocation, impossible travel detection, and configurable heuristics.
Face biometric verification is treated as a risk-reducing signal.

All thresholds are read from django.conf.settings so they can be
tuned via environment variables without code changes.
"""

import json
import urllib.request
import urllib.error
import math
import logging
from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from .models import LoginEvent, TrustedDevice, SecurityAlert

logger = logging.getLogger(__name__)


# ============================================================
# Geolocation Helper
# ============================================================

def get_ip_location(ip_address):
    """
    Resolve an IP address to country / city / lat / lon.

    Falls back to mock coordinates for loopback / private-network IPs
    to prevent crashes during local testing (per project rules).
    """
    default_location = {
        'country': 'Bangladesh',
        'city': 'Dhaka',
        'lat': 23.8103,
        'lon': 90.4125,
    }

    # Mock locations useful for testing impossible-travel flows
    mock_locations = {
        '127.0.0.1': default_location,
        'localhost': default_location,
        '8.8.8.8': {
            'country': 'United States',
            'city': 'Mountain View',
            'lat': 37.3860,
            'lon': -122.0838,
        },
        '1.1.1.1': {
            'country': 'Australia',
            'city': 'Sydney',
            'lat': -33.8688,
            'lon': 151.2093,
        },
    }

    if not ip_address:
        return default_location

    if ip_address in mock_locations:
        return mock_locations[ip_address]

    # Private subnets → default mock (rule #3)
    private_prefixes = ('192.168.', '10.', '172.16.', '172.17.', '172.18.',
                        '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                        '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                        '172.29.', '172.30.', '172.31.')
    if ip_address.startswith(private_prefixes):
        return default_location

    try:
        req = urllib.request.Request(
            f"http://ip-api.com/json/{ip_address}",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=2.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'lat': data.get('lat', 23.8103),
                        'lon': data.get('lon', 90.4125),
                    }
    except Exception as exc:
        logger.warning("GeoIP lookup failed for %s: %s", ip_address, exc)

    return default_location


# ============================================================
# Haversine
# ============================================================

def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres between two coordinate pairs."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ============================================================
# User-Agent Parser (lightweight, no extra dependency)
# ============================================================

def parse_user_agent(ua_string):
    """
    Minimal extraction of browser name and OS from a User-Agent header.
    Returns (browser, os_name).
    """
    if not ua_string:
        return ('Unknown', 'Unknown')

    ua = ua_string.lower()

    # Browser detection
    if 'edg/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome' in ua and 'edg/' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    else:
        browser = 'Other'

    # OS detection
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua:
        os_name = 'macOS'
    elif 'linux' in ua:
        os_name = 'Linux'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    else:
        os_name = 'Other'

    return (browser, os_name)


# ============================================================
# Risk Engine
# ============================================================

class BehavioralRiskEngine:
    """Evaluates risk score and level for logins and transactions."""

    @staticmethod
    def calculate_login_risk(user, ip_address, user_agent, browser, os_name,
                             device_fingerprint, face_verified=False):
        """
        Score a login attempt.

        Returns dict:
            score        – 0..100
            level        – 'low' | 'medium' | 'high'
            impossible_travel – bool
            reasons      – list[str]
            location     – dict with country/city/lat/lon
        """
        score = 0
        reasons = []
        impossible_travel = False
        location = get_ip_location(ip_address)

        # Read thresholds from settings
        speed_threshold = getattr(settings, 'IMPOSSIBLE_TRAVEL_SPEED_KMH', 800)
        fail_threshold = getattr(settings, 'FAILED_LOGIN_THRESHOLD', 3)
        fail_window = getattr(settings, 'FAILED_LOGIN_WINDOW_MINUTES', 10)

        # ------ 1. New / unrecognised device ------
        if user:
            known = TrustedDevice.objects.filter(
                user=user,
                device_fingerprint=device_fingerprint,
                trust_status=TrustedDevice.STATUS_TRUSTED,
            ).exists()
            if not known:
                score += 25
                reasons.append("New/Unrecognised device fingerprint")
        else:
            score += 40
            reasons.append("Login attempt for unknown user account")

        # ------ 2. Compare with last successful login ------
        last_ok = None
        if user:
            last_ok = (
                LoginEvent.objects
                .filter(user=user, is_successful=True)
                .order_by('-created_at')
                .first()
            )

        if last_ok:
            if last_ok.browser and browser != last_ok.browser:
                score += 10
                reasons.append(
                    f"Different browser (was {last_ok.browser}, now {browser})")

            if last_ok.os and os_name != last_ok.os:
                score += 15
                reasons.append(
                    f"Different OS (was {last_ok.os}, now {os_name})")

            if last_ok.country != location['country']:
                score += 20
                reasons.append(
                    f"Different country (was {last_ok.country}, "
                    f"now {location['country']})")

            # ------ 3. Impossible travel ------
            prev_loc = get_ip_location(last_ok.ip_address)
            dist = haversine(
                prev_loc['lat'], prev_loc['lon'],
                location['lat'], location['lon'],
            )
            elapsed_h = (
                (timezone.now() - last_ok.created_at).total_seconds() / 3600.0
            )
            if dist > 10 and elapsed_h > 0:
                speed = dist / elapsed_h
                if speed > speed_threshold:
                    impossible_travel = True
                    score += 45
                    reasons.append(
                        f"Impossible travel ({speed:.0f} km/h over "
                        f"{dist:.0f} km)")

        # ------ 4. Recent failed logins from this IP ------
        window_start = timezone.now() - timedelta(minutes=fail_window)
        fails = LoginEvent.objects.filter(
            ip_address=ip_address,
            is_successful=False,
            created_at__gte=window_start,
        ).count()
        if fails >= fail_threshold:
            score += 25
            reasons.append(
                f"{fails} failed logins from this IP in last {fail_window}m")

        # ------ 5. Unusual hours ------
        hour = timezone.now().hour
        if 2 <= hour <= 5:
            score += 10
            reasons.append("Unusual access hour (02:00–05:00)")

        # ------ 6. Face biometric bonus (reduces risk) ------
        if face_verified:
            score = max(score - 20, 0)
            reasons.append("Face biometric verified (−20 risk)")

        # ------ Clamp & categorise ------
        final = min(max(score, 0), 100)

        threshold_med = getattr(settings, 'RISK_THRESHOLD_MEDIUM', 30)
        threshold_hi = getattr(settings, 'RISK_THRESHOLD_HIGH', 70)

        if final <= threshold_med:
            level = LoginEvent.RISK_LEVEL_LOW
        elif final <= threshold_hi:
            level = LoginEvent.RISK_LEVEL_MEDIUM
        else:
            level = LoginEvent.RISK_LEVEL_HIGH

        # Auto-create alert for high risk
        if level == LoginEvent.RISK_LEVEL_HIGH and user:
            SecurityAlert.objects.create(
                user=user,
                alert_type='HIGH_RISK_LOGIN',
                severity=SecurityAlert.SEVERITY_HIGH,
                message=(
                    f"High-risk login for {user.email}. "
                    f"Score {final}. {'; '.join(reasons)}"
                ),
            )

        return {
            'score': final,
            'level': level,
            'impossible_travel': impossible_travel,
            'reasons': reasons,
            'location': location,
        }

    @staticmethod
    def calculate_transaction_risk(user, amount):
        """
        Score a financial transaction (transfer / withdrawal).

        Returns dict:  score, level, reasons.
        """
        score = 0
        reasons = []
        large_threshold = getattr(settings, 'LARGE_TRANSACTION_AMOUNT', 5000)

        # Transfer within 10 min of login
        last_login = (
            LoginEvent.objects
            .filter(user=user, is_successful=True)
            .order_by('-created_at')
            .first()
        )
        if last_login:
            mins_since = (
                (timezone.now() - last_login.created_at).total_seconds() / 60
            )
            if mins_since <= 10:
                score += 20
                reasons.append("Transaction within 10 min of login")

        # Large amount
        if float(amount) > large_threshold:
            score += 25
            reasons.append(
                f"Amount {amount} exceeds threshold {large_threshold}")

        # High ratio of balance
        try:
            if hasattr(user, 'ledger') and user.ledger.balance > 0:
                ratio = float(amount) / float(user.ledger.balance)
                if ratio > 0.8:
                    score += 30
                    reasons.append(
                        f"Transferring {ratio*100:.0f}% of balance")
        except Exception:
            pass

        final = min(max(score, 0), 100)
        threshold_med = getattr(settings, 'RISK_THRESHOLD_MEDIUM', 30)
        threshold_hi = getattr(settings, 'RISK_THRESHOLD_HIGH', 70)

        if final <= threshold_med:
            level = 'low'
        elif final <= threshold_hi:
            level = 'medium'
        else:
            level = 'high'

        return {'score': final, 'level': level, 'reasons': reasons}
