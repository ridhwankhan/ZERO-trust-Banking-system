from rest_framework import serializers
from .models import User


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup response (read-only)."""
    pass


class TwoFactorEnableSerializer(serializers.Serializer):
    """Serializer for enabling 2FA after verification."""
    token = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="6-digit verification code from authenticator app"
    )
    
    def validate_token(self, value):
        """Validate TOTP token format."""
        if not value.isdigit():
            raise serializers.ValidationError("Token must contain only digits")
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for 2FA verification during login."""
    user_id = serializers.IntegerField(help_text="User ID from initial login")
    token = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="6-digit verification code from authenticator app"
    )
    backup_code = serializers.CharField(
        max_length=8,
        min_length=8,
        required=False,
        help_text="8-character backup code (alternative to TOTP)"
    )
    
    def validate(self, attrs):
        """Ensure either token or backup code is provided."""
        token = attrs.get('token')
        backup_code = attrs.get('backup_code')
        
        if not token and not backup_code:
            raise serializers.ValidationError(
                "Either TOTP token or backup code must be provided"
            )
        
        if token and backup_code:
            raise serializers.ValidationError(
                "Provide either TOTP token or backup code, not both"
            )
        
        return attrs


class TwoFactorDisableSerializer(serializers.Serializer):
    """Serializer for disabling 2FA."""
    password = serializers.CharField(
        write_only=True,
        help_text="User password for confirmation"
    )
    token = serializers.CharField(
        max_length=6,
        min_length=6,
        required=False,
        help_text="Current TOTP token for confirmation"
    )
    backup_code = serializers.CharField(
        max_length=8,
        min_length=8,
        required=False,
        help_text="Backup code for confirmation"
    )
    
    def validate(self, attrs):
        """Ensure password and either token or backup code are provided."""
        password = attrs.get('password')
        token = attrs.get('token')
        backup_code = attrs.get('backup_code')
        
        if not password:
            raise serializers.ValidationError("Password is required")
        
        if not token and not backup_code:
            raise serializers.ValidationError(
                "Either TOTP token or backup code must be provided"
            )
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    crypto_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'is_active', 'created_at', 'crypto_status']
        read_only_fields = ['id', 'created_at']
    
    def get_crypto_status(self, obj):
        return {
            'rsa': {
                'has_public_key': bool(obj.public_key),
                'has_encrypted_private_key': bool(obj.encrypted_private_key)
            },
            'ecc': {
                'has_public_key': bool(obj.ecc_public_key),
                'has_encrypted_private_key': bool(obj.ecc_encrypted_private_key)
            }
        }
