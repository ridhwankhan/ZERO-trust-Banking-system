from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import sys
import os

# Add crypto module to path
crypto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from .models import User
from .serializers import (
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    TwoFactorEnableSerializer
)
from crypto.totp import TOTP


class TwoFactorSetupView(generics.GenericAPIView):
    """Set up two-factor authentication for a user."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TwoFactorSetupSerializer
    
    def get(self, request):
        """Generate TOTP secret and QR code URI for setup."""
        user = request.user
        
        # Generate new TOTP secret
        totp = TOTP()
        secret = totp.secret
        
        # Generate backup codes
        backup_codes = totp.generate_backup_codes()
        
        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Secure Banking System"
        )
        
        # Store secret temporarily (not enabled yet)
        user.two_factor_secret = secret
        user.two_factor_backup_codes = ','.join(backup_codes)
        user.save()
        
        return Response({
            'secret': secret,
            'provisioning_uri': provisioning_uri,
            'backup_codes': backup_codes,
            'instructions': {
                'step1': 'Scan the QR code with your authenticator app',
                'step2': 'Enter the 6-digit code to verify setup',
                'step3': 'Save backup codes in a secure location',
                'step4': 'Enable 2FA after verification'
            }
        })
    
    def post(self, request):
        """Enable two-factor authentication after verification."""
        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        token = serializer.validated_data['token']
        
        if not user.two_factor_secret:
            return Response(
                {'error': 'TOTP secret not found. Please setup first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the token
        from .totp import verify_totp_token
        if verify_totp_token(user.two_factor_secret, token):
            user.two_factor_enabled = True
            user.save()
            
            return Response({
                'message': 'Two-factor authentication enabled successfully',
                'backup_codes_remaining': len(user.two_factor_backup_codes.split(',') if user.two_factor_backup_codes else [])
            })
        else:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorVerifyView(APIView):
    """Verify two-factor authentication token during login."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify 2FA token for login completion."""
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        token = serializer.validated_data['token']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify TOTP token
        from .totp import verify_totp_token
        if verify_totp_token(user.two_factor_secret, token):
            # Generate JWT tokens for authenticated user
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role,
                    'is_admin': user.is_admin,
                    'has_rsa_keys': bool(user.encrypted_private_key),
                    'has_ecc_keys': bool(user.ecc_encrypted_private_key),
                    'two_factor_enabled': True
                },
                'message': 'Two-factor authentication successful'
            })
        else:
            return Response(
                {'error': 'Invalid authentication code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorBackupView(APIView):
    """Use backup codes for 2FA recovery."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Verify backup code and disable 2FA if requested."""
        backup_code = request.data.get('backup_code')
        disable_2fa = request.data.get('disable_2fa', False)
        
        if not backup_code:
            return Response(
                {'error': 'Backup code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.two_factor_backup_codes:
            return Response(
                {'error': 'No backup codes available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check backup code
        backup_codes = user.two_factor_backup_codes.split(',')
        if backup_code in backup_codes:
            # Remove used backup code
            backup_codes.remove(backup_code)
            user.two_factor_backup_codes = ','.join(backup_codes) if backup_codes else ''
            
            # Disable 2FA if requested or no more backup codes
            if disable_2fa or not backup_codes:
                user.two_factor_enabled = False
                user.two_factor_secret = None
                user.two_factor_backup_codes = None
            
            user.save()
            
            return Response({
                'message': 'Backup code verified successfully',
                'backup_codes_remaining': len(backup_codes),
                'two_factor_disabled': disable_2fa or not backup_codes
            })
        else:
            return Response(
                {'error': 'Invalid backup code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorStatusView(APIView):
    """Get current 2FA status for user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return 2FA status information."""
        user = request.user
        
        return Response({
            'two_factor_enabled': user.two_factor_enabled,
            'has_secret': bool(user.two_factor_secret),
            'backup_codes_count': len(user.two_factor_backup_codes.split(',')) if user.two_factor_backup_codes else 0,
            'setup_required': user.two_factor_secret and not user.two_factor_enabled
        })
