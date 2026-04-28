import hashlib
import secrets
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from rsa import generate_keypair, serialize_public_key, encrypt_private_key, decrypt_private_key
from ecc import ECCEncryption, ecc_serialize_public_key, ecc_encrypt_private_key, ecc_decrypt_private_key


class KeyRotationManager:
    """
    Advanced key rotation system for secure key management.
    Handles RSA and ECC key rotation with proper encryption and verification.
    """
    
    def __init__(self, rotation_interval_days: int = 90):
        """
        Initialize key rotation manager.
        
        Args:
            rotation_interval_days: Days between automatic key rotations
        """
        self.rotation_interval = timedelta(days=rotation_interval_days)
        self.key_versions: Dict[int, Dict] = {}  # user_id -> key_version_info
    
    def should_rotate_keys(self, user_id: int, last_rotation: datetime) -> bool:
        """
        Check if keys should be rotated based on time interval.
        
        Args:
            user_id: User identifier
            last_rotation: Last rotation timestamp
            
        Returns:
            True if keys should be rotated
        """
        return datetime.now() - last_rotation >= self.rotation_interval
    
    def rotate_rsa_keys(self, user_id: int, old_private_key: Tuple, password: str) -> Dict:
        """
        Rotate RSA keys with secure encryption.
        
        Args:
            user_id: User identifier
            old_private_key: Old RSA private key tuple (d, n)
            password: User password for encryption
            
        Returns:
            Dictionary with new key information
        """
        # Generate new RSA key pair
        new_public_key, new_private_key = generate_keypair(bits=2048)
        
        # Create key version metadata
        key_version = {
            'version': self._get_next_version(user_id),
            'algorithm': 'RSA',
            'key_size': 2048,
            'created_at': datetime.now().isoformat(),
            'previous_version_hash': self._hash_key_data(old_private_key)
        }
        
        # Encrypt new private key with password
        encrypted_private_key = encrypt_private_key(new_private_key, password)
        
        # Serialize new public key
        public_key_str = serialize_public_key(new_public_key)
        
        # Store rotation metadata
        self.key_versions[user_id] = key_version
        
        return {
            'public_key': public_key_str,
            'encrypted_private_key': encrypted_private_key,
            'version_info': key_version,
            'rotation_successful': True
        }
    
    def rotate_ecc_keys(self, user_id: int, old_private_key: int, password: str) -> Dict:
        """
        Rotate ECC keys with secure encryption.
        
        Args:
            user_id: User identifier
            old_private_key: Old ECC private key
            password: User password for encryption
            
        Returns:
            Dictionary with new key information
        """
        # Generate new ECC key pair
        ecc = ECCEncryption()
        new_private_key, new_public_key = ecc.generate_keypair()
        
        # Create key version metadata
        key_version = {
            'version': self._get_next_version(user_id),
            'algorithm': 'ECC',
            'curve': 'secp256k1',  # Default curve
            'created_at': datetime.now().isoformat(),
            'previous_version_hash': self._hash_key_data(str(old_private_key))
        }
        
        # Encrypt new private key with password
        encrypted_private_key = ecc_encrypt_private_key(new_private_key, password)
        
        # Serialize new public key
        public_key_str = ecc_serialize_public_key(new_public_key)
        
        # Store rotation metadata
        self.key_versions[user_id] = key_version
        
        return {
            'public_key': public_key_str,
            'encrypted_private_key': encrypted_private_key,
            'version_info': key_version,
            'rotation_successful': True
        }
    
    def verify_key_integrity(self, user_id: int, public_key: str, private_key_data: str, password: str) -> Dict:
        """
        Verify the integrity and correctness of key pairs.
        
        Args:
            user_id: User identifier
            public_key: Serialized public key
            private_key_data: Encrypted private key data
            password: User password for decryption
            
        Returns:
            Dictionary with verification results
        """
        verification_result = {
            'integrity_check': False,
            'algorithm': None,
            'key_pair_valid': False,
            'verification_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Try RSA verification
            if 'RSA' in public_key or 'exponent' in public_key:
                verification_result['algorithm'] = 'RSA'
                
                # Decrypt private key
                private_key = decrypt_private_key(private_key_data, password)
                
                # Test encryption/decryption
                test_data = "integrity_test_" + str(int(time.time()))
                from rsa import encrypt, decrypt
                encrypted = encrypt(test_data, eval(public_key))  # Parse public key
                decrypted = decrypt(encrypted, private_key)
                
                verification_result['key_pair_valid'] = (decrypted == test_data)
                verification_result['integrity_check'] = True
                
            # Try ECC verification
            else:
                verification_result['algorithm'] = 'ECC'
                
                # Decrypt private key
                private_key = ecc_decrypt_private_key(private_key_data, password)
                
                # Test encryption/decryption
                ecc = ECCEncryption()
                test_data = "integrity_test_" + str(int(time.time()))
                public_key_obj = ecc.deserialize_public_key(public_key)
                encrypted = ecc.encrypt(test_data, public_key_obj)
                decrypted = ecc.decrypt(encrypted, private_key)
                
                verification_result['key_pair_valid'] = (decrypted == test_data)
                verification_result['integrity_check'] = True
                
        except Exception as e:
            verification_result['error'] = str(e)
            verification_result['integrity_check'] = False
        
        return verification_result
    
    def get_key_rotation_history(self, user_id: int) -> List[Dict]:
        """
        Get the rotation history for a user's keys.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of rotation events
        """
        # In a real implementation, this would query a database
        # For now, return stored version information
        if user_id in self.key_versions:
            return [self.key_versions[user_id]]
        return []
    
    def schedule_rotation(self, user_id: int, scheduled_time: datetime) -> Dict:
        """
        Schedule a key rotation for a specific time.
        
        Args:
            user_id: User identifier
            scheduled_time: When to perform the rotation
            
        Returns:
            Schedule confirmation
        """
        return {
            'user_id': user_id,
            'scheduled_time': scheduled_time.isoformat(),
            'rotation_type': 'scheduled',
            'status': 'pending'
        }
    
    def _get_next_version(self, user_id: int) -> int:
        """Get the next version number for a user's keys."""
        if user_id in self.key_versions:
            return self.key_versions[user_id].get('version', 0) + 1
        return 1
    
    @staticmethod
    def _hash_key_data(key_data) -> str:
        """Create a hash of key data for verification."""
        if isinstance(key_data, tuple):
            key_str = str(key_data)
        else:
            key_str = str(key_data)
        
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    @staticmethod
    def generate_key_fingerprint(public_key: str) -> str:
        """
        Generate a unique fingerprint for a public key.
        
        Args:
            public_key: Serialized public key
            
        Returns:
            SHA-256 fingerprint
        """
        return hashlib.sha256(public_key.encode()).hexdigest()[:16]


class SecureKeyStorage:
    """
    Enhanced secure key storage with rotation support.
    """
    
    @staticmethod
    def re_encrypt_private_key(
        encrypted_key: str, 
        old_password: str, 
        new_password: str
    ) -> str:
        """
        Re-encrypt a private key with a new password.
        
        Args:
            encrypted_key: Currently encrypted private key
            old_password: Current password
            new_password: New password
            
        Returns:
            Re-encrypted private key
        """
        try:
            # Decrypt with old password
            private_key = decrypt_private_key(encrypted_key, old_password)
            
            # Re-encrypt with new password
            return encrypt_private_key(private_key, new_password)
            
        except Exception:
            # Try ECC decryption if RSA fails
            try:
                private_key = ecc_decrypt_private_key(encrypted_key, old_password)
                return ecc_encrypt_private_key(private_key, new_password)
            except Exception as e:
                raise ValueError(f"Key re-encryption failed: {str(e)}")


# Global key rotation manager instance
key_rotation_manager = KeyRotationManager()
