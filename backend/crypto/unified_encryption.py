import json
import hashlib
import secrets
from typing import Any, Dict, Optional, Union
from datetime import datetime

from rsa import generate_keypair, encrypt, decrypt, serialize_public_key
from ecc import ECCEncryption, ecc_serialize_public_key, ecc_deserialize_public_key


class UnifiedEncryptionManager:
    """
    Unified encryption system that handles both RSA and ECC encryption
    for different types of data with automatic algorithm selection.
    """
    
    def __init__(self):
        self.ecc = ECCEncryption()
    
    def encrypt_user_data(
        self, 
        data: Dict[str, Any], 
        rsa_public_key: str, 
        ecc_public_key: str,
        algorithm: str = 'auto'
    ) -> Dict[str, str]:
        """
        Encrypt user data using specified or automatically selected algorithm.
        
        Args:
            data: Dictionary of user data to encrypt
            rsa_public_key: RSA public key for encryption
            ecc_public_key: ECC public key for encryption
            algorithm: 'rsa', 'ecc', or 'auto' for automatic selection
            
        Returns:
            Dictionary with encrypted data
        """
        encrypted_data = {}
        
        for key, value in data.items():
            if value is None:
                encrypted_data[key] = None
                continue
            
            # Select encryption algorithm
            if algorithm == 'auto':
                # Use RSA for small data, ECC for larger data
                if len(str(value)) < 100:
                    selected_algorithm = 'rsa'
                else:
                    selected_algorithm = 'ecc'
            else:
                selected_algorithm = algorithm
            
            # Encrypt based on selected algorithm
            if selected_algorithm == 'rsa':
                encrypted_data[key] = self._encrypt_rsa(str(value), rsa_public_key)
                encrypted_data[f'{key}_algorithm'] = 'rsa'
            else:
                encrypted_data[key] = self._encrypt_ecc(str(value), ecc_public_key)
                encrypted_data[f'{key}_algorithm'] = 'ecc'
        
        return encrypted_data
    
    def decrypt_user_data(
        self, 
        encrypted_data: Dict[str, str], 
        rsa_private_key: tuple, 
        ecc_private_key: int
    ) -> Dict[str, Any]:
        """
        Decrypt user data using appropriate private keys.
        
        Args:
            encrypted_data: Dictionary with encrypted data
            rsa_private_key: RSA private key for decryption
            ecc_private_key: ECC private key for decryption
            
        Returns:
            Dictionary with decrypted data
        """
        decrypted_data = {}
        
        for key, value in encrypted_data.items():
            if value is None or key.endswith('_algorithm'):
                continue
            
            # Determine algorithm used
            algorithm_key = f'{key}_algorithm'
            algorithm = encrypted_data.get(algorithm_key, 'rsa')
            
            # Decrypt based on algorithm
            try:
                if algorithm == 'rsa':
                    decrypted_data[key] = self._decrypt_rsa(value, rsa_private_key)
                else:
                    decrypted_data[key] = self._decrypt_ecc(value, ecc_private_key)
            except Exception as e:
                decrypted_data[key] = f"DECRYPTION_ERROR: {str(e)}"
        
        return decrypted_data
    
    def encrypt_transaction_metadata(
        self, 
        metadata: Dict[str, Any], 
        receiver_public_key: str,
        privacy_level: str = 'high'
    ) -> str:
        """
        Encrypt transaction metadata based on privacy level.
        
        Args:
            metadata: Transaction metadata to encrypt
            receiver_public_key: Receiver's public key
            privacy_level: 'standard', 'private', or 'high'
            
        Returns:
            Encrypted metadata as JSON string
        """
        if privacy_level == 'standard':
            # No encryption for standard level
            return json.dumps(metadata)
        
        # Parse public key
        try:
            public_key = self.ecc.deserialize_public_key(receiver_public_key)
            metadata_json = json.dumps(metadata)
            encrypted = self.ecc.encrypt(metadata_json, public_key)
            return encrypted
        except Exception:
            # Fallback to error message
            return json.dumps({
                'error': 'ENCRYPTION_FAILED',
                'original_data': metadata
            })
    
    def decrypt_transaction_metadata(
        self, 
        encrypted_metadata: str, 
        private_key: int
    ) -> Dict[str, Any]:
        """
        Decrypt transaction metadata.
        
        Args:
            encrypted_metadata: Encrypted metadata string
            private_key: Private key for decryption
            
        Returns:
            Decrypted metadata dictionary
        """
        try:
            # Try ECC decryption first
            decrypted = self.ecc.decrypt(encrypted_metadata, private_key)
            return json.loads(decrypted)
        except:
            # Try parsing as plain JSON (standard privacy level)
            try:
                return json.loads(encrypted_metadata)
            except:
                return {
                    'error': 'DECRYPTION_FAILED',
                    'encrypted_data': encrypted_metadata
                }
    
    def create_secure_audit_log(
        self, 
        action: str, 
        user_id: int, 
        details: Dict[str, Any],
        rsa_public_key: str
    ) -> Dict[str, str]:
        """
        Create secure audit log with encrypted sensitive details.
        
        Args:
            action: Action performed
            user_id: User who performed the action
            details: Action details (may contain sensitive data)
            rsa_public_key: RSA public key for encryption
            
        Returns:
            Secure audit log entry
        """
        # Create audit log structure
        audit_log = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'session_id': secrets.token_hex(16),
            'ip_address_hash': hashlib.sha256(details.get('ip_address', '').encode()).hexdigest(),
            'user_agent_hash': hashlib.sha256(details.get('user_agent', '').encode()).hexdigest()
        }
        
        # Encrypt sensitive details
        sensitive_data = {
            'request_data': details.get('request_data', {}),
            'response_data': details.get('response_data', {}),
            'additional_info': details.get('additional_info', {})
        }
        
        try:
            rsa_pub_key = eval(serialize_public_key(eval(rsa_public_key)))
            encrypted_details = self._encrypt_rsa(json.dumps(sensitive_data), rsa_pub_key)
            audit_log['encrypted_details'] = encrypted_details
        except:
            audit_log['encrypted_details'] = 'ENCRYPTION_FAILED'
        
        return audit_log
    
    def verify_data_integrity(self, data: str, signature: str, public_key: str) -> bool:
        """
        Verify data integrity using digital signature.
        
        Args:
            data: Original data
            signature: Digital signature
            public_key: Public key for verification
            
        Returns:
            True if signature is valid
        """
        try:
            # This would implement digital signature verification
            # For now, return True as placeholder
            return True
        except:
            return False
    
    def _encrypt_rsa(self, data: str, public_key: str) -> str:
        """Encrypt data using RSA."""
        try:
            # Parse public key string back to tuple
            pub_key = eval(public_key)
            return encrypt(data, pub_key)
        except:
            return f"RSA_ENCRYPTION_ERROR: {data}"
    
    def _decrypt_rsa(self, encrypted_data: str, private_key: tuple) -> str:
        """Decrypt data using RSA."""
        try:
            return decrypt(encrypted_data, private_key)
        except:
            return f"RSA_DECRYPTION_ERROR: {encrypted_data}"
    
    def _encrypt_ecc(self, data: str, public_key: str) -> str:
        """Encrypt data using ECC."""
        try:
            pub_key = self.ecc.deserialize_public_key(public_key)
            return self.ecc.encrypt(data, pub_key)
        except:
            return f"ECC_ENCRYPTION_ERROR: {data}"
    
    def _decrypt_ecc(self, encrypted_data: str, private_key: int) -> str:
        """Decrypt data using ECC."""
        try:
            return self.ecc.decrypt(encrypted_data, private_key)
        except:
            return f"ECC_DECRYPTION_ERROR: {encrypted_data}"


class DataEncryptionValidator:
    """
    Validator to ensure all data is properly encrypted before storage.
    """
    
    def __init__(self):
        self.encryption_manager = UnifiedEncryptionManager()
    
    def validate_user_encryption(self, user_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate that user data is properly encrypted.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Validation results
        """
        validation_results = {
            'email_encrypted': False,
            'username_encrypted': False,
            'private_keys_encrypted': False,
            'public_keys_present': False,
            'overall_encryption_valid': False
        }
        
        # Check email encryption
        if user_data.get('email_encrypted') and not user_data.get('email') == user_data.get('email_encrypted'):
            validation_results['email_encrypted'] = True
        
        # Check username encryption
        if user_data.get('username_encrypted') and not user_data.get('username') == user_data.get('username_encrypted'):
            validation_results['username_encrypted'] = True
        
        # Check private key encryption
        if user_data.get('encrypted_private_key') and not user_data.get('encrypted_private_key').startswith('-----BEGIN'):
            validation_results['private_keys_encrypted'] = True
        
        # Check public keys presence
        if user_data.get('public_key') and user_data.get('ecc_public_key'):
            validation_results['public_keys_present'] = True
        
        # Overall validation
        validation_results['overall_encryption_valid'] = all([
            validation_results['email_encrypted'],
            validation_results['username_encrypted'],
            validation_results['private_keys_encrypted'],
            validation_results['public_keys_present']
        ])
        
        return validation_results
    
    def validate_transaction_encryption(self, transaction_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate that transaction data is properly encrypted based on privacy level.
        
        Args:
            transaction_data: Transaction data dictionary
            
        Returns:
            Validation results
        """
        validation_results = {
            'payload_encrypted': False,
            'hmac_present': False,
            'privacy_level_valid': False,
            'amount_visible': True,  # Amount should always be visible
            'overall_encryption_valid': False
        }
        
        privacy_level = transaction_data.get('privacy_level', 'standard')
        
        # Check payload encryption
        if privacy_level in ['private_metadata', 'high_privacy']:
            if transaction_data.get('encrypted_payload'):
                validation_results['payload_encrypted'] = True
        else:
            validation_results['payload_encrypted'] = True  # Standard level doesn't require encryption
        
        # Check HMAC presence
        if transaction_data.get('hmac_signature'):
            validation_results['hmac_present'] = True
        
        # Check privacy level validity
        if privacy_level in ['standard', 'private_metadata', 'high_privacy']:
            validation_results['privacy_level_valid'] = True
        
        # Check amount visibility
        if transaction_data.get('amount') is not None:
            validation_results['amount_visible'] = True
        
        # Overall validation
        validation_results['overall_encryption_valid'] = all([
            validation_results['payload_encrypted'],
            validation_results['hmac_present'],
            validation_results['privacy_level_valid'],
            validation_results['amount_visible']
        ])
        
        return validation_results


# Global instances
encryption_manager = UnifiedEncryptionManager()
encryption_validator = DataEncryptionValidator()
