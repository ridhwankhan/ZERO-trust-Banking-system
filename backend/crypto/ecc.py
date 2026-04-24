"""
Elliptic Curve Cryptography (ECC) implementation from scratch.
Implements secp256k1-like curve (simplified for clarity).
No external crypto libraries used.
"""
import random
import hashlib
import base64
import json
from typing import Tuple, Optional, List


class Point:
    """Represents a point on the elliptic curve."""
    def __init__(self, x: int, y: int, curve=None):
        self.x = x
        self.y = y
        self.curve = curve
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    
    def is_infinity(self) -> bool:
        """Check if this is the point at infinity (identity element)."""
        return self.x is None and self.y is None


class EllipticCurve:
    """
    Elliptic Curve: y^2 = x^3 + ax + b (mod p)
    
    We use a simplified curve similar to secp256k1 but with smaller parameters
    for reasonable performance in pure Python.
    """
    
    def __init__(self, a: int, b: int, p: int, gx: int, gy: int, n: int, h: int = 1):
        """
        Initialize curve parameters.
        
        Args:
            a: Curve parameter
            b: Curve parameter
            p: Prime modulus
            gx, gy: Base point (generator) coordinates
            n: Order of the base point
            h: Cofactor
        """
        self.a = a
        self.b = b
        self.p = p
        self.G = Point(gx, gy, self)  # Generator point
        self.n = n  # Order
        self.h = h  # Cofactor
    
    def is_on_curve(self, point: Point) -> bool:
        """Check if a point is on the curve."""
        if point.is_infinity():
            return True
        
        y_squared = (point.y * point.y) % self.p
        x_cubed = (point.x * point.x * point.x) % self.p
        ax = (self.a * point.x) % self.p
        
        return y_squared == (x_cubed + ax + self.b) % self.p
    
    def point_add(self, P: Point, Q: Point) -> Point:
        """
        Add two points on the curve.
        P + Q = R
        """
        # If either point is at infinity, return the other
        if P.is_infinity():
            return Q
        if Q.is_infinity():
            return P
        
        # If P == Q, use point doubling
        if P == Q:
            return self.point_double(P)
        
        # If P == -Q, return infinity
        if P.x == Q.x and P.y == (-Q.y) % self.p:
            return Point(None, None, self)
        
        # Calculate slope: s = (Qy - Py) / (Qx - Px) mod p
        numerator = (Q.y - P.y) % self.p
        denominator = (Q.x - P.x) % self.p
        s = (numerator * self._mod_inverse(denominator, self.p)) % self.p
        
        # Calculate Rx = s^2 - Px - Qx mod p
        rx = (s * s - P.x - Q.x) % self.p
        
        # Calculate Ry = s(Px - Rx) - Py mod p
        ry = (s * (P.x - rx) - P.y) % self.p
        
        return Point(rx, ry, self)
    
    def point_double(self, P: Point) -> Point:
        """
        Double a point on the curve (P + P).
        """
        if P.is_infinity() or P.y == 0:
            return Point(None, None, self)
        
        # Calculate slope: s = (3*Px^2 + a) / (2*Py) mod p
        numerator = (3 * P.x * P.x + self.a) % self.p
        denominator = (2 * P.y) % self.p
        s = (numerator * self._mod_inverse(denominator, self.p)) % self.p
        
        # Calculate Rx = s^2 - 2*Px mod p
        rx = (s * s - 2 * P.x) % self.p
        
        # Calculate Ry = s(Px - Rx) - Py mod p
        ry = (s * (P.x - rx) - P.y) % self.p
        
        return Point(rx, ry, self)
    
    def scalar_multiply(self, k: int, P: Point) -> Point:
        """
        Multiply a point by a scalar (k * P) using double-and-add algorithm.
        """
        if k % self.n == 0 or P.is_infinity():
            return Point(None, None, self)
        
        result = Point(None, None, self)
        addend = P
        
        # Convert to positive
        k = k % self.n
        
        while k:
            if k & 1:
                result = self.point_add(result, addend)
            addend = self.point_double(addend)
            k >>= 1
        
        return result
    
    def _mod_inverse(self, k: int, p: int) -> int:
        """Calculate modular multiplicative inverse using Extended Euclidean Algorithm."""
        if k < 0:
            k = k % p
        
        # Extended Euclidean Algorithm
        old_r, r = k, p
        old_s, s = 1, 0
        
        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s
        
        return old_s % p
    
    def generate_keypair(self) -> Tuple[int, Point]:
        """
        Generate ECC key pair.
        
        Returns:
            (private_key, public_key) where private_key is a scalar,
            public_key is a point on the curve
        """
        # Generate random private key [1, n-1]
        private_key = random.randint(1, self.n - 1)
        
        # Calculate public key: Q = d * G
        public_key = self.scalar_multiply(private_key, self.G)
        
        return private_key, public_key


# Define a curve with smaller parameters for reasonable performance
# These are NOT cryptographically secure parameters (too small for production)
# but demonstrate the ECC math correctly
SECP256K1_SIMPLIFIED = EllipticCurve(
    a=0,
    b=7,
    p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,  # Prime near 2^256
    gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
    n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,  # Order
    h=1
)


class ECCEncryption:
    """ECC-based encryption using ECIES (Elliptic Curve Integrated Encryption Scheme) approach."""
    
    def __init__(self, curve: EllipticCurve = SECP256K1_SIMPLIFIED):
        self.curve = curve
    
    def generate_keypair(self) -> Tuple[int, Point]:
        """Generate ECC key pair."""
        return self.curve.generate_keypair()
    
    def serialize_public_key(self, public_key: Point) -> str:
        """Serialize public key point to string."""
        if public_key.is_infinity():
            return json.dumps({'x': None, 'y': None})
        return json.dumps({'x': public_key.x, 'y': public_key.y})
    
    def deserialize_public_key(self, key_str: str) -> Point:
        """Deserialize public key from string."""
        data = json.loads(key_str)
        if data['x'] is None or data['y'] is None:
            return Point(None, None, self.curve)
        return Point(data['x'], data['y'], self.curve)
    
    def serialize_private_key(self, private_key: int) -> str:
        """Serialize private key to hex string."""
        return hex(private_key)
    
    def deserialize_private_key(self, key_str: str) -> int:
        """Deserialize private key from hex string."""
        return int(key_str, 16)
    
    def _derive_shared_secret(self, private_key: int, public_key: Point) -> bytes:
        """
        Derive shared secret using ECDH.
        Shared secret is the x-coordinate of (private_key * public_key)
        """
        shared_point = self.curve.scalar_multiply(private_key, public_key)
        if shared_point.is_infinity():
            raise ValueError("Invalid shared secret: point at infinity")
        
        # Use x-coordinate as shared secret, hash it
        shared_secret_bytes = shared_point.x.to_bytes(32, byteorder='big')
        return hashlib.sha256(shared_secret_bytes).digest()
    
    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption with key expansion."""
        key_expanded = key * ((len(data) // len(key)) + 1)
        return bytes(a ^ b for a, b in zip(data, key_expanded))
    
    def encrypt(self, message: str, recipient_public_key: Point) -> str:
        """
        Encrypt a message using ECIES-like scheme.
        
        1. Generate ephemeral key pair
        2. Derive shared secret using ECDH
        3. Encrypt message with XOR using derived key
        4. Return ephemeral public key + ciphertext
        """
        # Generate ephemeral key pair
        ephemeral_private = random.randint(1, self.curve.n - 1)
        ephemeral_public = self.curve.scalar_multiply(ephemeral_private, self.curve.G)
        
        # Derive shared secret
        shared_secret = self._derive_shared_secret(ephemeral_private, recipient_public_key)
        
        # Encrypt message
        message_bytes = message.encode('utf-8')
        ciphertext = self._xor_encrypt(message_bytes, shared_secret)
        
        # Package: ephemeral_public_key + ciphertext
        result = {
            'ephemeral_x': ephemeral_public.x,
            'ephemeral_y': ephemeral_public.y,
            'ciphertext': base64.b64encode(ciphertext).decode('ascii')
        }
        return json.dumps(result)
    
    def decrypt(self, encrypted_data: str, recipient_private_key: int) -> str:
        """
        Decrypt a message using ECIES-like scheme.
        
        1. Extract ephemeral public key and ciphertext
        2. Derive shared secret using ECDH (private_key * ephemeral_public)
        3. Decrypt message
        """
        data = json.loads(encrypted_data)
        
        # Reconstruct ephemeral public key
        ephemeral_public = Point(data['ephemeral_x'], data['ephemeral_y'], self.curve)
        
        # Derive shared secret
        shared_secret = self._derive_shared_secret(recipient_private_key, ephemeral_public)
        
        # Decrypt message
        ciphertext = base64.b64decode(data['ciphertext'])
        message_bytes = self._xor_encrypt(ciphertext, shared_secret)
        
        return message_bytes.decode('utf-8')


class ECCKeyManager:
    """Manages encryption/decryption of ECC private keys using password-derived keys."""
    
    @staticmethod
    def derive_key(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """Derive a key from password using PBKDF2 with SHA256."""
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    
    @classmethod
    def encrypt_private_key(cls, private_key: int, password: str) -> str:
        """
        Encrypt an ECC private key using a password-derived key.
        Returns a JSON string with salt and encrypted key.
        """
        # Generate random salt
        salt = random.randbytes(16)
        
        # Derive key from password
        derived_key = cls.derive_key(password, salt)
        
        # Convert private key to bytes (32 bytes for 256-bit key)
        key_bytes = private_key.to_bytes(32, byteorder='big')
        
        # XOR encryption with derived key
        derived_key_expanded = derived_key * ((len(key_bytes) // len(derived_key)) + 1)
        encrypted_bytes = bytes(a ^ b for a, b in zip(key_bytes, derived_key_expanded))
        
        # Package result
        result = {
            'salt': base64.b64encode(salt).decode('ascii'),
            'iterations': 100000,
            'encrypted_key': base64.b64encode(encrypted_bytes).decode('ascii')
        }
        return json.dumps(result)
    
    @classmethod
    def decrypt_private_key(cls, encrypted_data: str, password: str) -> int:
        """
        Decrypt an ECC private key using a password.
        Returns the decrypted private key integer.
        """
        try:
            data = json.loads(encrypted_data)
            salt = base64.b64decode(data['salt'])
            iterations = data.get('iterations', 100000)
            encrypted_bytes = base64.b64decode(data['encrypted_key'])
            
            # Derive key from password
            derived_key = cls.derive_key(password, salt, iterations)
            
            # XOR decryption
            derived_key_expanded = derived_key * ((len(encrypted_bytes) // len(derived_key)) + 1)
            decrypted_bytes = bytes(a ^ b for a, b in zip(encrypted_bytes, derived_key_expanded))
            
            # Convert back to integer
            return int.from_bytes(decrypted_bytes, byteorder='big')
        except Exception as e:
            raise ValueError(f"Failed to decrypt ECC private key: {str(e)}")


# Convenience functions for easy import
ecc_generate_keypair = ECCEncryption.generate_keypair
ecc_serialize_public_key = ECCEncryption.serialize_public_key
ecc_deserialize_public_key = ECCEncryption.deserialize_public_key
ecc_serialize_private_key = ECCEncryption.serialize_private_key
ecc_deserialize_private_key = ECCEncryption.deserialize_private_key
ecc_encrypt = ECCEncryption.encrypt
ecc_decrypt = ECCEncryption.decrypt
ecc_encrypt_private_key = ECCKeyManager.encrypt_private_key
ecc_decrypt_private_key = ECCKeyManager.decrypt_private_key
