import hashlib
import hmac
import time
import base64
import secrets
import struct
from typing import Optional


class TOTP:
    """
    Time-based One-Time Password implementation from scratch.
    Implements RFC 6238 TOTP algorithm without using external libraries.
    """
    
    def __init__(self, secret: Optional[str] = None, digits: int = 6, period: int = 30):
        """
        Initialize TOTP.
        
        Args:
            secret: Base32 encoded secret key (generated if None)
            digits: Number of digits in OTP (default: 6)
            period: Time period in seconds (default: 30)
        """
        self.digits = digits
        self.period = period
        self.secret = secret or self.generate_secret()
    
    def generate_secret(self) -> str:
        """Generate a random base32-encoded secret."""
        # Generate 160-bit random secret (20 bytes)
        random_bytes = secrets.token_bytes(20)
        # Convert to base32
        base32_secret = base64.b32encode(random_bytes).decode('utf-8')
        # Remove padding
        return base32_secret.rstrip('=')
    
    @staticmethod
    def hotp(secret: bytes, counter: int, digits: int = 6) -> str:
        """
        Generate HMAC-based One-Time Password (HOTP).
        
        Args:
            secret: Secret key as bytes
            counter: Counter value
            digits: Number of digits in OTP
            
        Returns:
            HOTP as string
        """
        # Convert counter to bytes (big-endian)
        counter_bytes = struct.pack('>Q', counter)
        
        # Calculate HMAC-SHA1
        hmac_hash = hmac.new(secret, counter_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation (RFC 4226 section 5.4)
        offset = hmac_hash[-1] & 0x0F
        binary = (
            (hmac_hash[offset] & 0x7F) << 24 |
            (hmac_hash[offset + 1] & 0xFF) << 16 |
            (hmac_hash[offset + 2] & 0xFF) << 8 |
            (hmac_hash[offset + 3] & 0xFF)
        )
        
        # Generate OTP with specified digits
        otp = binary % (10 ** digits)
        return str(otp).zfill(digits)
    
    def generate(self, timestamp: Optional[int] = None) -> str:
        """
        Generate TOTP for current time.
        
        Args:
            timestamp: Unix timestamp (uses current time if None)
            
        Returns:
            TOTP as string
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Calculate time step
        time_step = timestamp // self.period
        
        # Decode base32 secret
        secret_bytes = base64.b32decode(self.secret + '=' * ((8 - len(self.secret) % 8) % 8))
        
        # Generate HOTP
        return self.hotp(secret_bytes, time_step, self.digits)
    
    def verify(self, token: str, timestamp: Optional[int] = None, window: int = 1) -> bool:
        """
        Verify TOTP token with time window.
        
        Args:
            token: Token to verify
            timestamp: Unix timestamp (uses current time if None)
            window: Time window to allow (default: 1 = ±30 seconds)
            
        Returns:
            True if token is valid
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Check tokens within time window
        for offset in range(-window, window + 1):
            test_timestamp = timestamp + (offset * self.period)
            if self.generate(test_timestamp) == token:
                return True
        
        return False
    
    def provisioning_uri(self, name: str, issuer_name: str = "Banking App") -> str:
        """
        Generate QR code URI for TOTP setup.
        
        Args:
            name: User identifier (email)
            issuer_name: Application name
            
        Returns:
            otpauth:// URI for QR code generation
        """
        import urllib.parse
        
        params = {
            'secret': self.secret,
            'issuer': issuer_name,
            'algorithm': 'SHA1',
            'digits': str(self.digits),
            'period': str(self.period)
        }
        
        query_string = urllib.parse.urlencode(params)
        return f'otpauth://totp/{urllib.parse.quote(name)}?{query_string}'
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """
        Generate backup codes for 2FA recovery.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric backup code
            code = ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))
            codes.append(code)
        return codes


def generate_totp_secret() -> str:
    """Generate a new TOTP secret."""
    totp = TOTP()
    return totp.secret


def verify_totp_token(secret: str, token: str, window: int = 1) -> bool:
    """Verify a TOTP token."""
    totp = TOTP(secret)
    return totp.verify(token, window=window)
