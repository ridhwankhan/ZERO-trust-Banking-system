from rest_framework import serializers
from .models import User


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
