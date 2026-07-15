import json
import base64
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import WebAuthnCredential
from apps.users.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    UserVerificationRequirement,
    AuthenticatorSelectionCriteria,
    AuthenticatorAttachment
)

def bytes_to_b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

def b64url_to_bytes(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)

RP_ID = getattr(settings, 'WEBAUTHN_RP_ID', 'localhost')
RP_NAME = getattr(settings, 'WEBAUTHN_RP_NAME', 'Fiducia Bank')
ORIGIN = getattr(settings, 'WEBAUTHN_ORIGIN', 'http://localhost:5174') 
# Update ORIGIN based on environment, typically handled via env vars in prod

class WebAuthnRegisterOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get existing credentials to exclude them
        existing_credentials = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = [
            {"id": cred.credential_id, "type": "public-key"} 
            for cred in existing_credentials
        ]

        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=str(user.id).encode(),
            user_name=user.email,
            user_display_name=user.email,
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED
            ),
        )
        
        # Save challenge to cache for verification
        cache.set(f"webauthn_reg_challenge_{user.id}", options.challenge, timeout=300)

        return Response(json.loads(options_to_json(options)))


class WebAuthnRegisterVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        expected_challenge = cache.get(f"webauthn_reg_challenge_{user.id}")
        if not expected_challenge:
            return Response({"error": "Challenge expired"}, status=400)
            
        try:
            credential_data = request.data
            verification = verify_registration_response(
                credential=credential_data,
                expected_challenge=expected_challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
                require_user_verification=False,
            )
            
            # Save the new credential
            WebAuthnCredential.objects.create(
                user=user,
                credential_id=credential_data.get('id'), 
                public_key=bytes_to_b64url(verification.credential_public_key),
                sign_count=verification.sign_count,
            )
            
            return Response({"status": "ok"})
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class WebAuthnAuthOptionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email required"}, status=400)
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
            
        creds = WebAuthnCredential.objects.filter(user=user)
        if not creds.exists():
            return Response({"error": "No passkeys enrolled"}, status=404)
            
        allow_credentials = [
            {"id": c.credential_id, "type": "public-key"} for c in creds
        ]

        options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        
        cache.set(f"webauthn_auth_challenge_{user.id}", options.challenge, timeout=300)
        
        return Response(json.loads(options_to_json(options)))


class WebAuthnAuthVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        credential_data = request.data.get('credential')
        
        if not email or not credential_data:
            return Response({"error": "Missing data"}, status=400)
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
            
        expected_challenge = cache.get(f"webauthn_auth_challenge_{user.id}")
        if not expected_challenge:
            return Response({"error": "Challenge expired"}, status=400)
            
        try:
            cred_obj = None
            for c in WebAuthnCredential.objects.filter(user=user):
                if c.credential_id == credential_data.get('id'):
                    cred_obj = c
                    break
                    
            if not cred_obj:
                return Response({"error": "Credential not found"}, status=404)
                
            verification = verify_authentication_response(
                credential=credential_data,
                expected_challenge=expected_challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
                credential_public_key=b64url_to_bytes(cred_obj.public_key),
                credential_current_sign_count=cred_obj.sign_count,
            )
            
            # Update sign count
            cred_obj.sign_count = verification.new_sign_count
            cred_obj.save()
            
            # Success! Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role
                }
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)
