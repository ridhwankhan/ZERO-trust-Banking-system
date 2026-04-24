"""
Custom HMAC (Hash-based Message Authentication Code) implementation from scratch.
Implements HMAC-SHA256 without using the built-in hmac module.

HMAC algorithm (RFC 2104):
HMAC(K, m) = H((K' ⊕ opad) || H((K' ⊕ ipad) || m))

Where:
- K is the secret key
- m is the message
- H is the cryptographic hash function (SHA-256)
- K' is the key padded to block size (64 bytes for SHA-256)
- ⊕ is XOR
- || is concatenation
- ipad is 0x36 repeated block size times
- opad is 0x5C repeated block size times
"""
import hashlib
import base64


class HMACError(Exception):
    """Exception raised for HMAC-related errors."""
    pass


class HMAC:
    """
    HMAC implementation using SHA-256.
    Block size for SHA-256 is 64 bytes.
    """
    
    BLOCK_SIZE = 64  # 512 bits / 8 = 64 bytes for SHA-256
    IPAD_BYTE = 0x36
    OPAD_BYTE = 0x5C
    
    def __init__(self, key: bytes, message: bytes = None):
        """
        Initialize HMAC with key and optional message.
        
        Args:
            key: The secret key (bytes)
            message: The message to authenticate (bytes), optional
        """
        self.key = self._prepare_key(key)
        self.message = message or b''
        self._inner_hash = None
        self._outer_hash = None
    
    def _prepare_key(self, key: bytes) -> bytes:
        """
        Prepare the key for HMAC computation.
        If key is longer than block size, hash it first.
        If key is shorter than block size, pad with zeros.
        """
        if len(key) > self.BLOCK_SIZE:
            # Hash long keys
            key = hashlib.sha256(key).digest()
        
        # Pad key with zeros to block size
        if len(key) < self.BLOCK_SIZE:
            key = key + b'\x00' * (self.BLOCK_SIZE - len(key))
        
        return key
    
    def _create_ipad(self) -> bytes:
        """Create inner pad: key XOR 0x36 repeated."""
        return bytes(b ^ self.IPAD_BYTE for b in self.key)
    
    def _create_opad(self) -> bytes:
        """Create outer pad: key XOR 0x5C repeated."""
        return bytes(b ^ self.OPAD_BYTE for b in self.key)
    
    def compute(self, message: bytes = None) -> bytes:
        """
        Compute HMAC for the given message.
        
        Args:
            message: The message to authenticate (uses stored message if None)
        
        Returns:
            The HMAC as bytes (32 bytes for SHA-256)
        """
        if message is not None:
            self.message = message
        
        if not self.message:
            raise HMACError("No message provided for HMAC computation")
        
        # Step 1: Create ipad and opad
        ipad = self._create_ipad()
        opad = self._create_opad()
        
        # Step 2: Compute inner hash: H((K' ⊕ ipad) || message)
        inner_data = ipad + self.message
        self._inner_hash = hashlib.sha256(inner_data).digest()
        
        # Step 3: Compute outer hash: H((K' ⊕ opad) || inner_hash)
        outer_data = opad + self._inner_hash
        self._outer_hash = hashlib.sha256(outer_data).digest()
        
        return self._outer_hash
    
    def hexdigest(self, message: bytes = None) -> str:
        """
        Compute HMAC and return as hexadecimal string.
        
        Args:
            message: The message to authenticate (uses stored message if None)
        
        Returns:
            The HMAC as a hex string (64 characters for SHA-256)
        """
        hmac_bytes = self.compute(message)
        return hmac_bytes.hex()
    
    def b64digest(self, message: bytes = None) -> str:
        """
        Compute HMAC and return as base64 string.
        
        Args:
            message: The message to authenticate (uses stored message if None)
        
        Returns:
            The HMAC as a base64 string
        """
        hmac_bytes = self.compute(message)
        return base64.b64encode(hmac_bytes).decode('ascii')


class TransactionHMAC:
    """
    Specialized HMAC handler for transaction integrity.
    Generates and verifies HMAC signatures for transactions.
    """
    
    @staticmethod
    def generate_signature(
        secret_key: str,
        sender_id: int,
        receiver_id: int,
        amount: str,
        encrypted_payload: str,
        timestamp: str
    ) -> str:
        """
        Generate HMAC signature for a transaction.
        
        Args:
            secret_key: The secret key for HMAC
            sender_id: Transaction sender ID
            receiver_id: Transaction receiver ID
            amount: Transaction amount as string
            encrypted_payload: Encrypted transaction payload
            timestamp: Transaction timestamp
        
        Returns:
            Hex string of HMAC signature
        """
        # Create canonical message format
        message_parts = [
            str(sender_id),
            str(receiver_id),
            str(amount),
            encrypted_payload if encrypted_payload else '',
            timestamp
        ]
        
        # Use delimiter that won't appear in data
        message = '||'.join(message_parts)
        message_bytes = message.encode('utf-8')
        key_bytes = secret_key.encode('utf-8')
        
        # Compute HMAC
        hmac = HMAC(key_bytes, message_bytes)
        return hmac.hexdigest()
    
    @staticmethod
    def verify_signature(
        stored_signature: str,
        secret_key: str,
        sender_id: int,
        receiver_id: int,
        amount: str,
        encrypted_payload: str,
        timestamp: str
    ) -> bool:
        """
        Verify HMAC signature for a transaction.
        
        Args:
            stored_signature: The stored HMAC signature to verify against
            secret_key: The secret key for HMAC
            sender_id: Transaction sender ID
            receiver_id: Transaction receiver ID
            amount: Transaction amount as string
            encrypted_payload: Encrypted transaction payload
            timestamp: Transaction timestamp
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = TransactionHMAC.generate_signature(
                secret_key, sender_id, receiver_id, amount, 
                encrypted_payload, timestamp
            )
            
            # Use constant-time comparison to prevent timing attacks
            return HMACUtils.constant_time_compare(stored_signature, expected_signature)
        except Exception:
            return False


class HMACUtils:
    """Utility functions for HMAC operations."""
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """
        Compare two strings in constant time to prevent timing attacks.
        
        Args:
            a: First string
            b: Second string
        
        Returns:
            True if strings are equal, False otherwise
        """
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    @staticmethod
    def generate_random_key(length: int = 32) -> str:
        """
        Generate a random key for HMAC.
        
        Args:
            length: Key length in bytes (default 32 for SHA-256)
        
        Returns:
            Hex string of random key
        """
        import secrets
        return secrets.token_hex(length)


# Convenience functions for easy import
def compute_hmac(key: str, message: str) -> str:
    """
    Compute HMAC-SHA256 for a message with a key.
    
    Args:
        key: The secret key (string)
        message: The message to authenticate (string)
    
    Returns:
        Hex string of HMAC
    """
    hmac = HMAC(key.encode('utf-8'), message.encode('utf-8'))
    return hmac.hexdigest()


def verify_hmac(key: str, message: str, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature.
    
    Args:
        key: The secret key (string)
        message: The message to authenticate (string)
        signature: The expected HMAC signature (hex string)
    
        Returns:
            True if signature is valid
    """
    expected = compute_hmac(key, message)
    return HMACUtils.constant_time_compare(expected, signature)


def generate_transaction_signature(
    secret_key: str,
    sender_id: int,
    receiver_id: int,
    amount: str,
    encrypted_payload: str = '',
    timestamp: str = ''
) -> str:
    """
    Generate HMAC signature for transaction integrity.
    Convenience wrapper for TransactionHMAC.generate_signature.
    """
    return TransactionHMAC.generate_signature(
        secret_key, sender_id, receiver_id, amount, 
        encrypted_payload or '', timestamp
    )


def verify_transaction_signature(
    stored_signature: str,
    secret_key: str,
    sender_id: int,
    receiver_id: int,
    amount: str,
    encrypted_payload: str = '',
    timestamp: str = ''
) -> bool:
    """
    Verify HMAC signature for transaction integrity.
    Convenience wrapper for TransactionHMAC.verify_signature.
    """
    return TransactionHMAC.verify_signature(
        stored_signature, secret_key, sender_id, receiver_id,
        amount, encrypted_payload or '', timestamp
    )
