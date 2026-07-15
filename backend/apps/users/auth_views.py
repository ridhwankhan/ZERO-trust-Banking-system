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
    ChangePasswordSerializer,
    ProfileUpdateSerializer
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
        # Extract device/network info before validation (needed for fail logging too)
        ip_address = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT', '')
        face_hash = request.META.get('HTTP_X_FACE_SIGNATURE', '')

        # Lazy import to keep security module decoupled
        from apps.security.risk_engine import BehavioralRiskEngine, parse_user_agent, get_ip_location
        from apps.security.models import LoginEvent, TrustedDevice
        from apps.security.adaptive_auth import (
            get_required_verification, notify_new_device_login,
            notify_high_risk_login,
        )

        browser, os_name = parse_user_agent(user_agent)

        # --- Attempt authentication ---
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        except Exception as auth_exc:
            # Record failed login event
            email_attempted = request.data.get('email', '')
            user_obj = None
            try:
                user_obj = User.objects.get(email=email_attempted)
            except User.DoesNotExist:
                pass
            location = get_ip_location(ip_address)
            LoginEvent.objects.create(
                user=user_obj,
                email_entered=email_attempted,
                ip_address=ip_address,
                user_agent=user_agent,
                browser=browser,
                os=os_name,
                device_fingerprint=device_fingerprint,
                country=location['country'],
                city=location['city'],
                latitude=location['lat'],
                longitude=location['lon'],
                is_successful=False,
            )
            raise auth_exc  # Re-raise so DRF returns normal error response

        # --- Authentication succeeded ---
        data = serializer.validated_data

        # Extract and store private keys in memory (remove from response)
        rsa_private_key = data.pop('_rsa_private_key', None)
        ecc_private_key = data.pop('_ecc_private_key', None)
        user_id = data.get('user', {}).get('id')

        if user_id and (rsa_private_key or ecc_private_key):
            store_private_keys_in_session(user_id, rsa_private_key, ecc_private_key)

        # Resolve logged-in user object
        user_obj = User.objects.get(id=user_id) if user_id else None

        # --- Risk evaluation ---
        face_verified = bool(face_hash)
        risk_result = BehavioralRiskEngine.calculate_login_risk(
            user=user_obj,
            ip_address=ip_address,
            user_agent=user_agent,
            browser=browser,
            os_name=os_name,
            device_fingerprint=device_fingerprint,
            face_verified=face_verified,
        )
        location = risk_result['location']

        # Record successful login event
        LoginEvent.objects.create(
            user=user_obj,
            email_entered=request.data.get('email', ''),
            ip_address=ip_address,
            user_agent=user_agent,
            browser=browser,
            os=os_name,
            device_fingerprint=device_fingerprint,
            face_biometric_verified=face_verified,
            face_signature_hash=face_hash or None,
            country=location['country'],
            city=location['city'],
            latitude=location['lat'],
            longitude=location['lon'],
            risk_score=risk_result['score'],
            risk_level=risk_result['level'],
            risk_reasons=risk_result['reasons'],
            impossible_travel_detected=risk_result['impossible_travel'],
            is_successful=True,
        )

        # Register / update trusted device
        if user_obj and device_fingerprint:
            device, created = TrustedDevice.objects.get_or_create(
                user=user_obj,
                device_fingerprint=device_fingerprint,
                defaults={
                    'browser': browser,
                    'os': os_name,
                    'name': f"{browser} on {os_name}",
                    'has_face_biometric': face_verified,
                    'face_signature_hash': face_hash or None,
                },
            )
            if not created:
                device.browser = browser
                device.os = os_name
                device.save()
            else:
                # New device → email notification
                notify_new_device_login(user_obj, {
                    'browser': browser,
                    'os': os_name,
                    'ip': ip_address,
                    'city': location['city'],
                    'country': location['country'],
                })

        # High-risk → email notification
        if risk_result['level'] == 'high' and user_obj:
            notify_high_risk_login(
                user_obj, risk_result['score'], risk_result['reasons'])

        # Adaptive auth challenge info
        verification = get_required_verification(risk_result['level'], 'login')

        # Reformat response to match registration format
        response_data = {
            'tokens': {
                'access': data.pop('access'),
                'refresh': data.pop('refresh')
            },
            'user': data.get('user', {}),
            'security': {
                'risk_score': risk_result['score'],
                'risk_level': risk_result['level'],
                'risk_reasons': risk_result['reasons'],
                'impossible_travel': risk_result['impossible_travel'],
                'verification': verification,
            },
        }
        return Response(response_data, status=status.HTTP_200_OK)


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
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ProfileUpdateSerializer
        return UserProfileSerializer
    
    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(self.get_object(), context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = UserProfileSerializer(user, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)


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


# ==================== ADMIN/AUTHORITY AUTH ====================

class AdminLoginView(APIView):
    """Admin login endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Login as admin."""
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if admin
            if not user.is_admin:
                return Response(
                    {'error': 'Admin access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify password
            if not user.check_password(password):
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role,
                    'is_admin': user.is_admin,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                },
                'message': 'Admin login successful'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AuthorityLoginView(APIView):
    """Central Authority login endpoint."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Login as authority."""
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if authority
            if user.role != User.ROLE_AUTHORITY:
                return Response(
                    {'error': 'Authority access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify password
            if not user.check_password(password):
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                },
                'message': 'Authority login successful'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
