"""
Key Management System for secure handling of RSA and ECC private keys.

Features:
- Secure key storage (encrypted at rest)
- Password-derived key encryption
- Key re-encryption on password change
- Key recovery mechanisms
- In-memory key cache with expiration
"""
import json
import base64
import hashlib
import secrets
import time
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class KeyPair:
    """Represents a cryptographic key pair."""
    public_key: Any
    private_key: Any
    key_type: str  # 'rsa' or 'ecc'


class SecureKeyStorage:
    """
    Manages secure storage and retrieval of encrypted private keys.
    All private keys are stored encrypted - never plaintext.
    """
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: User's password
            salt: Random salt bytes
            iterations: PBKDF2 iteration count
        
        Returns:
            32-byte derived key
        """
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations
        )
    
    @classmethod
    def encrypt_private_key(
        cls,
        private_key: Any,
        password: str,
        key_type: str = 'rsa'
    ) -> str:
        """
        Encrypt a private key using password-derived key.
        
        Args:
            private_key: The private key to encrypt
            password: User's password
            key_type: 'rsa' or 'ecc'
        
        Returns:
            JSON string containing encrypted key data
        """
        # Generate random salt
        salt = secrets.token_bytes(16)
        
        # Derive key from password
        derived_key = cls.derive_key_from_password(password, salt)
        
        # Serialize private key based on type
        if key_type == 'rsa':
            # RSA key is a tuple (d, n)
            key_data = json.dumps({
                'd': str(private_key[0]),
                'n': str(private_key[1])
            }).encode('utf-8')
        elif key_type == 'ecc':
            # ECC key is an integer
            key_data = private_key.to_bytes(32, byteorder='big')
        else:
            raise ValueError(f"Unknown key type: {key_type}")
        
        # XOR encryption with derived key
        key_expanded = derived_key * ((len(key_data) // len(derived_key)) + 1)
        encrypted_bytes = bytes(a ^ b for a, b in zip(key_data, key_expanded[:len(key_data)]))
        
        # Package result
        result = {
            'salt': base64.b64encode(salt).decode('ascii'),
            'iterations': 100000,
            'key_type': key_type,
            'encrypted_data': base64.b64encode(encrypted_bytes).decode('ascii'),
            'version': '1.0'
        }
        return json.dumps(result)
    
    @classmethod
    def decrypt_private_key(
        cls,
        encrypted_package: str,
        password: str
    ) -> Tuple[Any, str]:
        """
        Decrypt a private key using password.
        
        Args:
            encrypted_package: JSON string from encrypt_private_key
            password: User's password
        
        Returns:
            Tuple of (private_key, key_type)
        
        Raises:
            ValueError: If decryption fails (wrong password or corrupted data)
        """
        try:
            data = json.loads(encrypted_package)
            
            salt = base64.b64decode(data['salt'])
            iterations = data.get('iterations', 100000)
            key_type = data.get('key_type', 'rsa')
            encrypted_bytes = base64.b64decode(data['encrypted_data'])
            
            # Derive key from password
            derived_key = cls.derive_key_from_password(password, salt, iterations)
            
            # XOR decryption
            key_expanded = derived_key * ((len(encrypted_bytes) // len(derived_key)) + 1)
            decrypted_bytes = bytes(a ^ b for a, b in zip(encrypted_bytes, key_expanded[:len(encrypted_bytes)]))
            
            # Deserialize based on key type
            if key_type == 'rsa':
                key_dict = json.loads(decrypted_bytes.decode('utf-8'))
                private_key = (int(key_dict['d']), int(key_dict['n']))
            elif key_type == 'ecc':
                private_key = int.from_bytes(decrypted_bytes, byteorder='big')
            else:
                raise ValueError(f"Unknown key type: {key_type}")
            
            return private_key, key_type
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt private key: {str(e)}")
    
    @classmethod
    def re_encrypt_private_key(
        cls,
        encrypted_package: str,
        old_password: str,
        new_password: str
    ) -> str:
        """
        Re-encrypt a private key with a new password.
        
        Args:
            encrypted_package: Current encrypted key data
            old_password: Current password for decryption
            new_password: New password for encryption
        
        Returns:
            New encrypted package with new password
        """
        # Decrypt with old password
        private_key, key_type = cls.decrypt_private_key(encrypted_package, old_password)
        
        # Re-encrypt with new password
        return cls.encrypt_private_key(private_key, new_password, key_type)


class InMemoryKeyCache:
    """
    Thread-safe in-memory cache for decrypted private keys.
    Keys are stored only in memory and automatically expire.
    """
    
    _cache: Dict[int, Dict[str, Any]] = {}
    _default_ttl: int = 3600  # 1 hour default TTL
    
    @classmethod
    def store_keys(
        cls,
        user_id: int,
        rsa_private_key: Optional[Tuple[int, int]] = None,
        ecc_private_key: Optional[int] = None,
        ttl: int = None
    ):
        """
        Store decrypted keys in memory cache.
        
        Args:
            user_id: User ID
            rsa_private_key: RSA private key tuple (d, n)
            ecc_private_key: ECC private key integer
            ttl: Time-to-live in seconds (default 1 hour)
        """
        expiry = time.time() + (ttl or cls._default_ttl)
        
        cls._cache[user_id] = {
            'rsa': rsa_private_key,
            'ecc': ecc_private_key,
            'expiry': expiry
        }
    
    @classmethod
    def get_keys(cls, user_id: int) -> Dict[str, Any]:
        """
        Retrieve keys from cache if not expired.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with 'rsa' and 'ecc' keys, or empty dict if expired/missing
        """
        entry = cls._cache.get(user_id)
        
        if entry is None:
            return {}
        
        # Check expiry
        if time.time() > entry['expiry']:
            cls.clear_keys(user_id)
            return {}
        
        return {
            'rsa': entry.get('rsa'),
            'ecc': entry.get('ecc')
        }
    
    @classmethod
    def get_rsa_key(cls, user_id: int) -> Optional[Tuple[int, int]]:
        """Get RSA private key from cache."""
        keys = cls.get_keys(user_id)
        return keys.get('rsa')
    
    @classmethod
    def get_ecc_key(cls, user_id: int) -> Optional[int]:
        """Get ECC private key from cache."""
        keys = cls.get_keys(user_id)
        return keys.get('ecc')
    
    @classmethod
    def clear_keys(cls, user_id: int):
        """Clear keys for a user from cache."""
        if user_id in cls._cache:
            del cls._cache[user_id]
    
    @classmethod
    def clear_all_keys(cls):
        """Clear all keys from cache (e.g., on server restart)."""
        cls._cache.clear()
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_users = [
            user_id for user_id, entry in cls._cache.items()
            if current_time > entry['expiry']
        ]
        for user_id in expired_users:
            del cls._cache[user_id]


class KeyRecoveryManager:
    """
    Manages key recovery mechanisms for password resets.
    
    Note: Without the old password, encrypted private keys cannot be recovered.
    This is by design for security. Recovery options:
    1. User must provide old password during password change
    2. Keys are regenerated if old password is lost (with user consent)
    """
    
    @staticmethod
    def can_recover_keys(
        encrypted_rsa_key: Optional[str],
        encrypted_ecc_key: Optional[str],
        old_password: str
    ) -> bool:
        """
        Check if keys can be recovered with provided old password.
        
        Args:
            encrypted_rsa_key: Encrypted RSA private key
            encrypted_ecc_key: Encrypted ECC private key
            old_password: Old password to attempt decryption
        
        Returns:
            True if keys can be decrypted with old password
        """
        try:
            if encrypted_rsa_key:
                SecureKeyStorage.decrypt_private_key(encrypted_rsa_key, old_password)
            if encrypted_ecc_key:
                SecureKeyStorage.decrypt_private_key(encrypted_ecc_key, old_password)
            return True
        except ValueError:
            return False
    
    @classmethod
    def recover_keys_with_password(
        cls,
        encrypted_rsa_key: Optional[str],
        encrypted_ecc_key: Optional[str],
        old_password: str,
        new_password: str
    ) -> Dict[str, str]:
        """
        Recover and re-encrypt keys during password change.
        
        Args:
            encrypted_rsa_key: Encrypted RSA private key
            encrypted_ecc_key: Encrypted ECC private key
            old_password: Current password for decryption
            new_password: New password for encryption
        
        Returns:
            Dict with 'rsa' and 'ecc' containing new encrypted packages
        
        Raises:
            ValueError: If old password cannot decrypt keys
        """
        result = {}
        
        if encrypted_rsa_key:
            result['rsa'] = SecureKeyStorage.re_encrypt_private_key(
                encrypted_rsa_key, old_password, new_password
            )
        
        if encrypted_ecc_key:
            result['ecc'] = SecureKeyStorage.re_encrypt_private_key(
                encrypted_ecc_key, old_password, new_password
            )
        
        return result
    
    @staticmethod
    def generate_recovery_summary(
        has_rsa_key: bool,
        has_ecc_key: bool,
        recovery_successful: bool
    ) -> Dict[str, Any]:
        """
        Generate a summary of key recovery status.
        
        Args:
            has_rsa_key: Whether user had RSA key
            has_ecc_key: Whether user had ECC key
            recovery_successful: Whether recovery succeeded
        
        Returns:
            Summary dict with status and warnings
        """
        summary = {
            'rsa_key': {
                'existed': has_rsa_key,
                'recovered': recovery_successful if has_rsa_key else False
            },
            'ecc_key': {
                'existed': has_ecc_key,
                'recovered': recovery_successful if has_ecc_key else False
            },
            'warnings': []
        }
        
        if has_rsa_key and not recovery_successful:
            summary['warnings'].append(
                'RSA private key could not be recovered. '
                'Old password required for recovery. '
                'New keys will need to be generated if old password is lost.'
            )
        
        if has_ecc_key and not recovery_successful:
            summary['warnings'].append(
                'ECC private key could not be recovered. '
                'Old password required for recovery. '
                'New keys will need to be generated if old password is lost.'
            )
        
        return summary


# Convenience functions for direct import
def store_user_keys(
    user_id: int,
    rsa_private_key: Optional[Tuple[int, int]] = None,
    ecc_private_key: Optional[int] = None,
    ttl: int = 3600
):
    """Store user keys in memory cache."""
    InMemoryKeyCache.store_keys(user_id, rsa_private_key, ecc_private_key, ttl)


def get_user_rsa_key(user_id: int) -> Optional[Tuple[int, int]]:
    """Get user's RSA private key from memory cache."""
    return InMemoryKeyCache.get_rsa_key(user_id)


def get_user_ecc_key(user_id: int) -> Optional[int]:
    """Get user's ECC private key from memory cache."""
    return InMemoryKeyCache.get_ecc_key(user_id)


def clear_user_keys(user_id: int):
    """Clear user's keys from memory cache (e.g., on logout)."""
    InMemoryKeyCache.clear_keys(user_id)


def re_encrypt_user_keys(
    encrypted_rsa_key: Optional[str],
    encrypted_ecc_key: Optional[str],
    old_password: str,
    new_password: str
) -> Dict[str, str]:
    """
    Re-encrypt user keys with new password.
    
    Returns:
        Dict with 'rsa' and 'ecc' keys containing new encrypted packages
    """
    return KeyRecoveryManager.recover_keys_with_password(
        encrypted_rsa_key, encrypted_ecc_key, old_password, new_password
    )
