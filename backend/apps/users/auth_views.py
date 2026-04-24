from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .auth_serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)

# Import key management system
import sys
import os
crypto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from key_management import (
    InMemoryKeyCache,
    store_user_keys,
    get_user_rsa_key,
    get_user_ecc_key,
    clear_user_keys
)

# Backwards compatibility wrappers
def store_private_keys_in_session(user_id: int, rsa_private_key: dict = None, ecc_private_key: int = None):
    """Store decrypted private keys in memory (delegates to key_management)."""
    rsa_tuple = None
    if rsa_private_key:
        rsa_tuple = (rsa_private_key['d'], rsa_private_key['n'])
    InMemoryKeyCache.store_keys(user_id, rsa_tuple, ecc_private_key)

def get_rsa_private_key_from_session(user_id: int) -> dict:
    """Retrieve decrypted RSA private key from memory."""
    key = InMemoryKeyCache.get_rsa_key(user_id)
    if key:
        return {'d': key[0], 'n': key[1]}
    return None

def get_ecc_private_key_from_session(user_id: int) -> int:
    """Retrieve decrypted ECC private key from memory."""
    return InMemoryKeyCache.get_ecc_key(user_id)

def clear_private_keys_from_session(user_id: int):
    """Clear decrypted private keys from memory (logout)."""
    InMemoryKeyCache.clear_keys(user_id)

# Alias for backwards compatibility
clear_private_key_from_session = clear_private_keys_from_session


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role,
                'crypto': {
                    'rsa': {
                        'public_key_set': bool(user.public_key),
                        'encrypted_private_key_set': bool(user.encrypted_private_key)
                    },
                    'ecc': {
                        'public_key_set': bool(user.ecc_public_key),
                        'encrypted_private_key_set': bool(user.ecc_encrypted_private_key)
                    }
                }
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            },
            'message': 'User registered successfully with RSA and ECC encryption'
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the validated data which includes private keys
        data = serializer.validated_data
        
        # Extract and store private keys in memory (remove from response)
        rsa_private_key = data.pop('_rsa_private_key', None)
        ecc_private_key = data.pop('_ecc_private_key', None)
        user_id = data.get('user', {}).get('id')
        
        if user_id and (rsa_private_key or ecc_private_key):
            store_private_keys_in_session(user_id, rsa_private_key, ecc_private_key)
        
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Clear decrypted private keys from memory (secure logout)
            clear_private_keys_from_session(request.user.id)
            
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {
                    'message': 'Successfully logged out',
                    'security_note': 'All private keys cleared from memory'
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            
            # Use serializer update to handle password change and key re-encryption
            serializer.update(user, serializer.validated_data)
            
            # Get key re-encryption results
            key_results = serializer.get_key_recovery_results()
            
            response_data = {
                'message': 'Password changed successfully',
                'key_management': {
                    'rsa_re_encrypted': key_results.get('rsa_re_encrypted', False),
                    'ecc_re_encrypted': key_results.get('ecc_re_encrypted', False)
                }
            }
            
            # Add warnings if any
            warnings = key_results.get('warnings', [])
            if warnings:
                response_data['warnings'] = warnings
                response_data['note'] = (
                    'Some encryption keys could not be re-encrypted. '
                    'Please login again to verify your keys are working. '
                    'If issues persist, contact support.'
                )
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
