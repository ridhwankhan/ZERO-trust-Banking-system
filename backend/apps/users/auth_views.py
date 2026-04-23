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

# In-memory storage for decrypted private keys (keyed by user_id)
# This stays only in memory and is cleared on server restart
_decrypted_keys_store = {}


def store_private_keys_in_session(user_id: int, rsa_private_key: dict = None, ecc_private_key: int = None):
    """Store decrypted private keys in memory (session-like storage)."""
    if user_id not in _decrypted_keys_store:
        _decrypted_keys_store[user_id] = {}
    
    if rsa_private_key:
        _decrypted_keys_store[user_id]['rsa'] = rsa_private_key
    if ecc_private_key:
        _decrypted_keys_store[user_id]['ecc'] = ecc_private_key


def get_rsa_private_key_from_session(user_id: int) -> dict:
    """Retrieve decrypted RSA private key from memory."""
    user_keys = _decrypted_keys_store.get(user_id, {})
    return user_keys.get('rsa')


def get_ecc_private_key_from_session(user_id: int) -> int:
    """Retrieve decrypted ECC private key from memory."""
    user_keys = _decrypted_keys_store.get(user_id, {})
    return user_keys.get('ecc')


def clear_private_keys_from_session(user_id: int):
    """Clear decrypted private keys from memory (logout)."""
    if user_id in _decrypted_keys_store:
        del _decrypted_keys_store[user_id]


# Backwards compatibility aliases
store_private_key_in_session = store_private_keys_in_session
get_private_key_from_session = get_rsa_private_key_from_session
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
            # Clear decrypted private keys from memory
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
                {'message': 'Successfully logged out'},
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
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
