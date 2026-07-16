import json
import base64
import logging
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
)
from webauthn.helpers.structs import (
    UserVerificationRequirement,
    AuthenticatorSelectionCriteria,
)

logger = logging.getLogger(__name__)


def bytes_to_b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')


def b64url_to_bytes(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)


def _webauthn_config():
    """Resolve RP settings at request time so env changes apply without import-order issues."""
    return (
        getattr(settings, 'WEBAUTHN_RP_ID', 'localhost'),
        getattr(settings, 'WEBAUTHN_RP_NAME', 'Fiducia Bank'),
        getattr(settings, 'WEBAUTHN_ORIGIN', 'http://localhost:5174'),
    )


class WebAuthnRegisterOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        rp_id, rp_name, _origin = _webauthn_config()

        existing_credentials = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = [
            {"id": cred.credential_id, "type": "public-key"}
            for cred in existing_credentials
        ]

        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=rp_name,
            user_id=str(user.id).encode(),
            user_name=user.email,
            user_display_name=user.email,
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED
            ),
        )

        cache.set(f"webauthn_reg_challenge_{user.id}", options.challenge, timeout=300)
        return Response(json.loads(options_to_json(options)))


class WebAuthnRegisterVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        rp_id, _rp_name, origin = _webauthn_config()
        expected_challenge = cache.get(f"webauthn_reg_challenge_{user.id}")
        if not expected_challenge:
            return Response({"error": "Challenge expired. Please try again."}, status=400)

        try:
            credential_data = request.data
            verification = verify_registration_response(
                credential=credential_data,
                expected_challenge=expected_challenge,
                expected_origin=origin,
                expected_rp_id=rp_id,
                require_user_verification=False,
            )

            WebAuthnCredential.objects.create(
                user=user,
                credential_id=credential_data.get('id'),
                public_key=bytes_to_b64url(verification.credential_public_key),
                sign_count=verification.sign_count,
            )

            return Response({"status": "ok"})

        except Exception as e:
            logger.exception("WebAuthn registration verify failed")
            return Response({"error": str(e)}, status=400)


class WebAuthnAuthOptionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        if not email:
            return Response({"error": "Email required"}, status=400)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "No account found for that email. Please register first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        creds = WebAuthnCredential.objects.filter(user=user)
        if not creds.exists():
            return Response(
                {
                    "error": (
                        "No passkey enrolled for this account. "
                        "Sign in with your password, then enroll a passkey in Security Center."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        rp_id, _rp_name, _origin = _webauthn_config()
        allow_credentials = [
            {"id": c.credential_id, "type": "public-key"} for c in creds
        ]

        options = generate_authentication_options(
            rp_id=rp_id,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )

        cache.set(f"webauthn_auth_challenge_{user.id}", options.challenge, timeout=300)
        return Response(json.loads(options_to_json(options)))


class WebAuthnAuthVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        credential_data = request.data.get('credential')

        if not email or not credential_data:
            return Response({"error": "Missing data"}, status=400)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "No account found for that email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_challenge = cache.get(f"webauthn_auth_challenge_{user.id}")
        if not expected_challenge:
            return Response({"error": "Challenge expired. Please try again."}, status=400)

        try:
            cred_obj = None
            for c in WebAuthnCredential.objects.filter(user=user):
                if c.credential_id == credential_data.get('id'):
                    cred_obj = c
                    break

            if not cred_obj:
                return Response(
                    {"error": "Passkey not recognized for this account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            rp_id, _rp_name, origin = _webauthn_config()
            verification = verify_authentication_response(
                credential=credential_data,
                expected_challenge=expected_challenge,
                expected_origin=origin,
                expected_rp_id=rp_id,
                credential_public_key=b64url_to_bytes(cred_obj.public_key),
                credential_current_sign_count=cred_obj.sign_count,
            )

            cred_obj.sign_count = verification.new_sign_count
            cred_obj.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role,
                    'two_factor_enabled': user.two_factor_enabled,
                }
            })

        except Exception as e:
            logger.exception("WebAuthn authentication verify failed")
            return Response({"error": str(e)}, status=400)
