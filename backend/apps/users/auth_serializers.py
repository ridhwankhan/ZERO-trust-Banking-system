from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
import sys
import os

# Import transactions models for KYC request
from apps.transactions.models import KYCRequest

# Add crypto module to path if needed
crypto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from rsa import (
    generate_keypair,
    encrypt,
    decrypt,
    encrypt_private_key as encrypt_rsa_private_key,
    serialize_public_key,
    deserialize_public_key,
    decrypt_private_key as decrypt_rsa_private_key
)

from ecc import (
    ecc_generate_keypair,
    ecc_serialize_public_key,
    ecc_encrypt_private_key,
    ecc_decrypt_private_key,
    ECCEncryption
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    contact_info = serializers.CharField(write_only=True, required=True)
    admin_code = serializers.CharField(write_only=True, required=False, help_text="Admin registration code for role-based access")

    class Meta:
        model = User
        fields = ('email', 'username', 'contact_info', 'password', 'password_confirm', 'role', 'admin_code')
        extra_kwargs = {
            'role': {'required': False, 'default': User.ROLE_USER}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        
        # Validate admin registration
        requested_role = attrs.get('role', User.ROLE_USER)
        admin_code = attrs.get('admin_code', '')
        
        if requested_role == User.ROLE_ADMIN:
            if not admin_code:
                raise serializers.ValidationError({
                    "admin_code": "Admin registration code is required for admin role."
                })
            if admin_code != 'ADMIN_SECRET_2024':  # In production, use environment variable
                raise serializers.ValidationError({
                    "admin_code": "Invalid admin registration code."
                })
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data.pop('admin_code', None)  # Remove admin_code from user creation
        password = validated_data['password']
        contact_info = validated_data['contact_info']
        
        # Generate RSA key pair
        rsa_public_key, rsa_private_key = generate_keypair(bits=1024)
        
        # Encrypt email and username with RSA public key
        email_encrypted = encrypt(validated_data['email'], rsa_public_key)
        username_encrypted = encrypt(validated_data['username'], rsa_public_key)
        contact_info_encrypted = encrypt(contact_info, rsa_public_key)
        
        # Encrypt RSA private key with password-derived key
        rsa_encrypted_private_key = encrypt_rsa_private_key(rsa_private_key, password)
        
        # Serialize RSA public key for storage
        rsa_public_key_str = serialize_public_key(rsa_public_key)
        
        # Generate ECC key pair
        ecc = ECCEncryption()
        ecc_private_key, ecc_public_key = ecc.generate_keypair()
        
        # Encrypt ECC private key with password-derived key
        ecc_encrypted_private_key = ecc_encrypt_private_key(ecc_private_key, password)
        
        # Serialize ECC public key for storage
        ecc_public_key_str = ecc.serialize_public_key(ecc_public_key)
        
        user = User.objects.create(
            email=validated_data['email'],  # Keep plaintext for Django auth
            username=validated_data['username'],  # Keep plaintext for Django auth
            contact_info=contact_info,
            contact_info_encrypted=contact_info_encrypted,
            email_encrypted=email_encrypted,
            username_encrypted=username_encrypted,
            public_key=rsa_public_key_str,
            encrypted_private_key=rsa_encrypted_private_key,
            ecc_public_key=ecc_public_key_str,
            ecc_encrypted_private_key=ecc_encrypted_private_key,
            role=User.ROLE_USER
        )
        user.set_password(password)
        user.save()
        
        # Auto-create KYC request for new user
        KYCRequest.objects.create(
            user=user,
            status=KYCRequest.STATUS_PENDING
        )
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        password = attrs.get('password')
        
        # Decrypt RSA private key using password
        decrypted_rsa_private_key = None
        if self.user.encrypted_private_key:
            try:
                decrypted_rsa_private_key = decrypt_rsa_private_key(
                    self.user.encrypted_private_key, 
                    password
                )
            except ValueError:
                pass
        
        # Decrypt ECC private key using password
        decrypted_ecc_private_key = None
        if self.user.ecc_encrypted_private_key:
            try:
                decrypted_ecc_private_key = ecc_decrypt_private_key(
                    self.user.ecc_encrypted_private_key,
                    password
                )
            except ValueError:
                pass
        
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'role': self.user.role,
            'is_admin': self.user.is_admin,
            'two_factor_enabled': self.user.two_factor_enabled,
            'has_rsa_keys': bool(self.user.encrypted_private_key),
            'has_ecc_keys': bool(self.user.ecc_encrypted_private_key)
        }
        
        # Store decrypted keys in session (only in memory, not in response)
        if decrypted_rsa_private_key:
            data['_rsa_private_key'] = {
                'd': decrypted_rsa_private_key[0],
                'n': decrypted_rsa_private_key[1]
            }
        
        if decrypted_ecc_private_key:
            data['_ecc_private_key'] = decrypted_ecc_private_key
        
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    contact_info = serializers.SerializerMethodField()
    crypto_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'contact_info',
            'role',
            'two_factor_enabled',
            'created_at',
            'updated_at',
            'crypto_status',
        )
        read_only_fields = (
            'id',
            'email',
            'username',
            'contact_info',
            'role',
            'two_factor_enabled',
            'created_at',
            'updated_at',
        )
    
    def get_contact_info(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Prefer decrypting from encrypted storage using in-memory RSA private key.
        if obj.contact_info_encrypted:
            try:
                from key_management import InMemoryKeyCache
                rsa_private_key = InMemoryKeyCache.get_rsa_key(obj.id)
                if rsa_private_key:
                    return decrypt(obj.contact_info_encrypted, rsa_private_key)
            except Exception:
                pass
        
        # Graceful fallback if in-memory key is unavailable.
        return obj.contact_info
    
    def get_crypto_status(self, obj):
        return {
            'rsa': {
                'has_public_key': bool(obj.public_key),
                'has_encrypted_private_key': bool(obj.encrypted_private_key),
                'has_encrypted_email': bool(obj.email_encrypted),
                'has_encrypted_username': bool(obj.username_encrypted),
                'has_encrypted_contact_info': bool(obj.contact_info_encrypted)
            },
            'ecc': {
                'has_public_key': bool(obj.ecc_public_key),
                'has_encrypted_private_key': bool(obj.ecc_encrypted_private_key)
            }
        }


class ProfileUpdateSerializer(serializers.ModelSerializer):
    contact_info = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ('email', 'username', 'contact_info')

    def update(self, instance, validated_data):
        new_email = validated_data.get('email', instance.email)
        new_username = validated_data.get('username', instance.username)
        new_contact_info = validated_data.get('contact_info', instance.contact_info or '')

        if not instance.public_key:
            raise serializers.ValidationError({
                'public_key': 'User public key is missing. Cannot encrypt profile fields.'
            })

        try:
            rsa_public_key = deserialize_public_key(instance.public_key)
        except Exception as exc:
            raise serializers.ValidationError({
                'public_key': f'Invalid public key format: {str(exc)}'
            })

        instance.email = new_email
        instance.username = new_username
        instance.contact_info = new_contact_info
        instance.email_encrypted = encrypt(new_email, rsa_public_key)
        instance.username_encrypted = encrypt(new_username, rsa_public_key)
        instance.contact_info_encrypted = encrypt(new_contact_info, rsa_public_key)
        instance.save(
            update_fields=[
                'email',
                'username',
                'contact_info',
                'email_encrypted',
                'username_encrypted',
                'contact_info_encrypted',
                'updated_at',
            ]
        )
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def update(self, instance, validated_data):
        """
        Update password and re-encrypt private keys with new password.
        """
        import sys
        import os
        
        # Add crypto path
        crypto_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'crypto'
        )
        if crypto_path not in sys.path:
            sys.path.insert(0, crypto_path)
        
        from key_management import (
            SecureKeyStorage,
            KeyRecoveryManager,
            InMemoryKeyCache
        )
        
        old_password = validated_data['old_password']
        new_password = validated_data['new_password']
        
        # Track key recovery status
        key_recovery_results = {
            'rsa_re_encrypted': False,
            'ecc_re_encrypted': False,
            'warnings': []
        }
        
        # Re-encrypt RSA private key if exists
        if instance.encrypted_private_key:
            try:
                new_rsa_encrypted = SecureKeyStorage.re_encrypt_private_key(
                    instance.encrypted_private_key,
                    old_password,
                    new_password
                )
                instance.encrypted_private_key = new_rsa_encrypted
                key_recovery_results['rsa_re_encrypted'] = True
            except ValueError as e:
                key_recovery_results['warnings'].append(
                    f"RSA key re-encryption failed: {str(e)}"
                )
        
        # Re-encrypt ECC private key if exists
        if instance.ecc_encrypted_private_key:
            try:
                new_ecc_encrypted = SecureKeyStorage.re_encrypt_private_key(
                    instance.ecc_encrypted_private_key,
                    old_password,
                    new_password
                )
                instance.ecc_encrypted_private_key = new_ecc_encrypted
                key_recovery_results['ecc_re_encrypted'] = True
            except ValueError as e:
                key_recovery_results['warnings'].append(
                    f"ECC key re-encryption failed: {str(e)}"
                )
        
        # Update password
        instance.set_password(new_password)
        instance.save()
        
        # Clear in-memory keys (user needs to re-login to decrypt with new password)
        InMemoryKeyCache.clear_keys(instance.id)
        
        # Store recovery results for response
        self._key_recovery_results = key_recovery_results
        
        return instance

    def get_key_recovery_results(self):
        """Get the results of key re-encryption."""
        return getattr(self, '_key_recovery_results', {})
