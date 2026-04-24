"""
RSA Implementation from scratch using only Python standard library.
No external crypto libraries used.
"""
import hashlib
import random
import base64
import json
from typing import Tuple, Optional


class RSA:
    """RSA encryption/decryption implementation."""
    
    # Small primes for initial filtering
    SMALL_PRIMES = [
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
        53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113
    ]
    
    @staticmethod
    def is_prime(n: int, k: int = 10) -> bool:
        """
        Miller-Rabin primality test.
        Returns True if n is probably prime.
        k determines accuracy (higher = more accurate).
        """
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        # Write n-1 as 2^r * d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2
        
        # Witness loop
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
            
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        
        return True
    
    @staticmethod
    def generate_large_prime(bits: int = 1024) -> int:
        """Generate a large prime number of specified bit length."""
        while True:
            # Generate random odd number with specified bit length
            n = random.getrandbits(bits)
            # Ensure it's odd and has the correct bit length
            n |= (1 << bits - 1) | 1
            
            # Quick check against small primes
            for p in RSA.SMALL_PRIMES:
                if n % p == 0:
                    break
            else:
                # Miller-Rabin test
                if RSA.is_prime(n, k=10):
                    return n
    
    @staticmethod
    def mod_inverse(e: int, phi: int) -> int:
        """Calculate modular multiplicative inverse using Extended Euclidean Algorithm."""
        def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y
        
        gcd, x, _ = extended_gcd(e % phi, phi)
        if gcd != 1:
            raise ValueError("Modular inverse does not exist")
        return x % phi
    
    @classmethod
    def generate_keypair(cls, bits: int = 1024) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Generate RSA public and private key pair.
        Returns: ((e, n), (d, n)) where (e, n) is public key, (d, n) is private key
        """
        # Generate two distinct primes
        p = cls.generate_large_prime(bits // 2)
        q = cls.generate_large_prime(bits // 2)
        
        while p == q:
            q = cls.generate_large_prime(bits // 2)
        
        n = p * q
        phi = (p - 1) * (q - 1)
        
        # Choose public exponent e (common value is 65537)
        e = 65537
        while cls._gcd(e, phi) != 1:
            e += 2
        
        # Calculate private exponent d
        d = cls.mod_inverse(e, phi)
        
        return ((e, n), (d, n))
    
    @staticmethod
    def _gcd(a: int, b: int) -> int:
        """Calculate greatest common divisor using Euclidean algorithm."""
        while b:
            a, b = b, a % b
        return a
    
    @classmethod
    def encrypt(cls, message: str, public_key: Tuple[int, int]) -> str:
        """
        Encrypt a message using RSA public key.
        Returns base64-encoded encrypted data.
        """
        e, n = public_key
        
        # Convert message to bytes, then to integer
        message_bytes = message.encode('utf-8')
        message_int = int.from_bytes(message_bytes, byteorder='big')
        
        # Check if message fits in key size
        if message_int >= n:
            raise ValueError("Message too long for key size. Use chunking for long messages.")
        
        # Encrypt: c = m^e mod n
        encrypted_int = pow(message_int, e, n)
        
        # Convert to bytes and encode as base64
        encrypted_bytes = encrypted_int.to_bytes((encrypted_int.bit_length() + 7) // 8, byteorder='big')
        return base64.b64encode(encrypted_bytes).decode('ascii')
    
    @classmethod
    def decrypt(cls, encrypted_data: str, private_key: Tuple[int, int]) -> str:
        """
        Decrypt data using RSA private key.
        Input should be base64-encoded encrypted data.
        """
        d, n = private_key
        
        # Decode base64 and convert to integer
        encrypted_bytes = base64.b64decode(encrypted_data)
        encrypted_int = int.from_bytes(encrypted_bytes, byteorder='big')
        
        # Decrypt: m = c^d mod n
        decrypted_int = pow(encrypted_int, d, n)
        
        # Convert back to bytes and then to string
        decrypted_bytes = decrypted_int.to_bytes((decrypted_int.bit_length() + 7) // 8, byteorder='big')
        return decrypted_bytes.decode('utf-8')
    
    @classmethod
    def encrypt_long_message(cls, message: str, public_key: Tuple[int, int], chunk_size: int = 100) -> str:
        """
        Encrypt a long message by chunking.
        Returns JSON string with encrypted chunks.
        """
        e, n = public_key
        max_chunk_size = (n.bit_length() // 8) - 11  # Leave some padding
        
        chunks = []
        message_bytes = message.encode('utf-8')
        
        for i in range(0, len(message_bytes), max_chunk_size):
            chunk = message_bytes[i:i + max_chunk_size]
            chunk_int = int.from_bytes(chunk, byteorder='big')
            encrypted_int = pow(chunk_int, e, n)
            encrypted_bytes = encrypted_int.to_bytes((encrypted_int.bit_length() + 7) // 8, byteorder='big')
            chunks.append(base64.b64encode(encrypted_bytes).decode('ascii'))
        
        return json.dumps(chunks)
    
    @classmethod
    def decrypt_long_message(cls, encrypted_data: str, private_key: Tuple[int, int]) -> str:
        """
        Decrypt a long message that was chunked.
        Input should be JSON string with encrypted chunks.
        """
        d, n = private_key
        chunks = json.loads(encrypted_data)
        
        decrypted_bytes = b''
        for chunk_b64 in chunks:
            chunk_bytes = base64.b64decode(chunk_b64)
            chunk_int = int.from_bytes(chunk_bytes, byteorder='big')
            decrypted_int = pow(chunk_int, d, n)
            decrypted_chunk = decrypted_int.to_bytes((decrypted_int.bit_length() + 7) // 8, byteorder='big')
            decrypted_bytes += decrypted_chunk
        
        return decrypted_bytes.decode('utf-8')


class KeyManager:
    """Manages encryption/decryption of RSA keys using password-derived keys."""
    
    @staticmethod
    def derive_key(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive a key from password using PBKDF2 with SHA256.
        """
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    
    @classmethod
    def encrypt_private_key(cls, private_key: Tuple[int, int], password: str) -> str:
        """
        Encrypt a private key using a password-derived key.
        Returns a JSON string with salt and encrypted key.
        """
        # Generate random salt
        salt = random.randbytes(16)
        
        # Derive key from password
        derived_key = cls.derive_key(password, salt)
        
        # Convert private key to bytes
        d, n = private_key
        key_data = f"{d},{n}".encode('utf-8')
        
        # XOR encryption with derived key (simple but effective)
        derived_key_expanded = derived_key * ((len(key_data) // len(derived_key)) + 1)
        encrypted_bytes = bytes(a ^ b for a, b in zip(key_data, derived_key_expanded))
        
        # Package result
        result = {
            'salt': base64.b64encode(salt).decode('ascii'),
            'iterations': 100000,
            'encrypted_key': base64.b64encode(encrypted_bytes).decode('ascii')
        }
        return json.dumps(result)
    
    @classmethod
    def decrypt_private_key(cls, encrypted_data: str, password: str) -> Tuple[int, int]:
        """
        Decrypt a private key using a password.
        Returns the decrypted private key tuple (d, n).
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
            
            # Parse private key
            key_str = decrypted_bytes.decode('utf-8').rstrip('\x00')
            d, n = map(int, key_str.split(','))
            return (d, n)
        except Exception as e:
            raise ValueError(f"Failed to decrypt private key: {str(e)}")
    
    @staticmethod
    def serialize_public_key(public_key: Tuple[int, int]) -> str:
        """Serialize public key to string format."""
        e, n = public_key
        return json.dumps({'e': e, 'n': n})
    
    @staticmethod
    def deserialize_public_key(key_str: str) -> Tuple[int, int]:
        """Deserialize public key from string format."""
        data = json.loads(key_str)
        return (data['e'], data['n'])


# Utility functions for easy import
generate_keypair = RSA.generate_keypair
encrypt = RSA.encrypt
decrypt = RSA.decrypt
encrypt_long_message = RSA.encrypt_long_message
decrypt_long_message = RSA.decrypt_long_message
encrypt_private_key = KeyManager.encrypt_private_key
decrypt_private_key = KeyManager.decrypt_private_key
serialize_public_key = KeyManager.serialize_public_key
deserialize_public_key = KeyManager.deserialize_public_key
