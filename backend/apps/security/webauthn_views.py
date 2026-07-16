import json
import logging
import os
from urllib.parse import urlparse

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

from apps.users.models import User
from .models import WebAuthnChallenge, WebAuthnCredential

logger = logging.getLogger(__name__)


def bytes_to_b64url(b: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')


def b64url_to_bytes(s: str) -> bytes:
    import base64
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)


def _webauthn_config(request=None):
    """Prefer browser Origin so Vercel production works without manual env vars."""
    rp_name = getattr(settings, 'WEBAUTHN_RP_NAME', 'Fiducia Bank')
    env_rp_id = os.getenv('WEBAUTHN_RP_ID') or getattr(settings, 'WEBAUTHN_RP_ID', 'localhost')
    env_origin = os.getenv('WEBAUTHN_ORIGIN') or getattr(settings, 'WEBAUTHN_ORIGIN', 'http://localhost:5174')

    if request is not None:
        header_origin = request.headers.get('Origin') or ''
        if not header_origin:
            referer = request.headers.get('Referer') or ''
            if referer:
                parsed_ref = urlparse(referer)
                if parsed_ref.scheme and parsed_ref.netloc:
                    header_origin = f'{parsed_ref.scheme}://{parsed_ref.netloc}'
        if header_origin:
            parsed = urlparse(header_origin)
            if parsed.hostname:
                return parsed.hostname, rp_name, f'{parsed.scheme}://{parsed.netloc}'.rstrip('/')

    return env_rp_id, rp_name, env_origin.rstrip('/')


def _save_challenge(user, purpose: str, challenge: bytes, rp_id: str, origin: str):
    WebAuthnChallenge.objects.update_or_create(
        user=user,
        purpose=purpose,
        defaults={
            'challenge': bytes_to_b64url(challenge),
            'rp_id': rp_id,
            'origin': origin,
        },
    )


def _pop_challenge(user, purpose: str):
    try:
        row = WebAuthnChallenge.objects.get(user=user, purpose=purpose)
    except WebAuthnChallenge.DoesNotExist:
        return None
    data = {
        'challenge': b64url_to_bytes(row.challenge),
        'rp_id': row.rp_id,
        'origin': row.origin,
    }
    row.delete()
    return data


def _credential_descriptors(creds):
    descriptors = []
    for c in creds:
        try:
            descriptors.append(
                PublicKeyCredentialDescriptor(id=b64url_to_bytes(c.credential_id))
            )
        except Exception:
            # Credential IDs from the browser are already base64url strings; if decoding
            # fails, try raw UTF-8 bytes as a last resort.
            descriptors.append(
                PublicKeyCredentialDescriptor(id=c.credential_id.encode('utf-8'))
            )
    return descriptors


class WebAuthnStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        creds = WebAuthnCredential.objects.filter(user=request.user)
        return Response({
            'enrolled': creds.exists(),
            'count': creds.count(),
            'credentials': [
                {
                    'id': c.id,
                    'device_name': c.device_name,
                    'created_at': c.created_at,
                    'last_used_at': c.last_used_at,
                    'credential_id_preview': (c.credential_id[:12] + '…') if c.credential_id else '',
                }
                for c in creds
            ],
        })


class WebAuthnClearView(APIView):
    """Remove all passkeys for the current user (so they can re-enroll / overwrite)."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        deleted, _ = WebAuthnCredential.objects.filter(user=request.user).delete()
        WebAuthnChallenge.objects.filter(user=request.user).delete()
        return Response({
            'status': 'ok',
            'deleted': deleted,
            'message': 'All passkeys removed. You can enroll a new one now.',
        })


class WebAuthnRegisterOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        rp_id, rp_name, origin = _webauthn_config(request)
        overwrite = str(request.query_params.get('overwrite', '')).lower() in ('1', 'true', 'yes')

        if overwrite:
            WebAuthnCredential.objects.filter(user=user).delete()

        existing = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = _credential_descriptors(existing) if not overwrite else []

        try:
            options = generate_registration_options(
                rp_id=rp_id,
                rp_name=rp_name,
                user_id=str(user.id).encode('utf-8'),
                user_name=user.email,
                user_display_name=user.email,
                exclude_credentials=exclude_credentials,
                authenticator_selection=AuthenticatorSelectionCriteria(
                    user_verification=UserVerificationRequirement.PREFERRED
                ),
            )
        except Exception as exc:
            logger.exception('Failed generating WebAuthn registration options')
            return Response({'error': f'Could not start biometric enrollment: {exc}'}, status=500)

        _save_challenge(user, WebAuthnChallenge.PURPOSE_REG, options.challenge, rp_id, origin)
        return Response(json.loads(options_to_json(options)))


class WebAuthnRegisterVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        pending = _pop_challenge(user, WebAuthnChallenge.PURPOSE_REG)
        if not pending:
            return Response({'error': 'Challenge expired. Please try enrollment again.'}, status=400)

        overwrite = bool(request.data.get('overwrite')) or str(
            request.query_params.get('overwrite', '')
        ).lower() in ('1', 'true', 'yes')

        try:
            # Browser may send the attestation either as the body itself or nested.
            credential_data = request.data.get('credential') or request.data
            verification = verify_registration_response(
                credential=credential_data,
                expected_challenge=pending['challenge'],
                expected_origin=pending['origin'],
                expected_rp_id=pending['rp_id'],
                require_user_verification=False,
            )

            cred_id = credential_data.get('id')
            if not cred_id:
                return Response({'error': 'Missing credential id from authenticator.'}, status=400)

            if overwrite:
                WebAuthnCredential.objects.filter(user=user).delete()

            # Replace same credential id if it already exists (re-enroll / overwrite)
            WebAuthnCredential.objects.filter(credential_id=cred_id).delete()
            WebAuthnCredential.objects.create(
                user=user,
                credential_id=cred_id,
                public_key=bytes_to_b64url(verification.credential_public_key),
                sign_count=verification.sign_count or 0,
                device_name=request.data.get('device_name') or 'Passkey Device',
            )

            return Response({
                'status': 'ok',
                'rp_id': pending['rp_id'],
                'message': 'Passkey enrolled successfully.',
            })
        except Exception as e:
            logger.exception('WebAuthn registration verify failed')
            return Response({'error': str(e)}, status=400)


class WebAuthnAuthOptionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        # Authenticated "verify my passkey" flow can omit email
        if not email and request.user and request.user.is_authenticated:
            email = request.user.email

        if not email:
            return Response({'error': 'Email required'}, status=400)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No account found for that email. Please register first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        creds = list(WebAuthnCredential.objects.filter(user=user))
        if not creds:
            return Response(
                {
                    'error': (
                        'No passkey enrolled for this account. '
                        'Sign in with your password, then enroll a passkey in Security Center.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        rp_id, _rp_name, origin = _webauthn_config(request)

        try:
            options = generate_authentication_options(
                rp_id=rp_id,
                allow_credentials=_credential_descriptors(creds),
                user_verification=UserVerificationRequirement.PREFERRED,
            )
        except Exception as exc:
            logger.exception('Failed generating WebAuthn auth options')
            return Response({'error': f'Could not start biometric login: {exc}'}, status=500)

        _save_challenge(user, WebAuthnChallenge.PURPOSE_AUTH, options.challenge, rp_id, origin)
        payload = json.loads(options_to_json(options))
        payload['email'] = user.email
        return Response(payload)


class WebAuthnAuthVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        credential_data = request.data.get('credential') or request.data.get('response') or request.data

        # Nested shape from frontend: { email, credential: asseResp }
        if isinstance(credential_data, dict) and 'credential' in credential_data and 'id' not in credential_data:
            credential_data = credential_data.get('credential')

        if request.user and request.user.is_authenticated and not email:
            email = request.user.email

        if not email:
            return Response({'error': 'Missing email'}, status=400)
        if not credential_data or not isinstance(credential_data, dict) or not credential_data.get('id'):
            return Response({'error': 'Missing credential data from authenticator'}, status=400)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found for that email.'}, status=400)

        pending = _pop_challenge(user, WebAuthnChallenge.PURPOSE_AUTH)
        if not pending:
            return Response({'error': 'Challenge expired. Please try biometric login again.'}, status=400)

        try:
            cred_obj = WebAuthnCredential.objects.filter(
                user=user,
                credential_id=credential_data.get('id'),
            ).first()
            if not cred_obj:
                return Response(
                    {'error': 'Passkey not recognized for this account. Re-enroll in Security Center.'},
                    status=400,
                )

            verification = verify_authentication_response(
                credential=credential_data,
                expected_challenge=pending['challenge'],
                expected_origin=pending['origin'],
                expected_rp_id=pending['rp_id'],
                credential_public_key=b64url_to_bytes(cred_obj.public_key),
                credential_current_sign_count=cred_obj.sign_count or 0,
                require_user_verification=False,
            )

            # Some platform authenticators keep sign_count at 0; never decrease it.
            new_count = verification.new_sign_count or 0
            if new_count >= (cred_obj.sign_count or 0):
                cred_obj.sign_count = new_count
            cred_obj.save(update_fields=['sign_count', 'last_used_at'])

            # Test/verify-only mode (Security Center) — do not issue tokens
            if request.data.get('verify_only'):
                return Response({
                    'status': 'ok',
                    'verified': True,
                    'message': 'Biometric verification successful.',
                    'user': {'id': user.id, 'email': user.email},
                })

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
                },
                'message': 'Passkey login successful',
            })
        except Exception as e:
            logger.exception('WebAuthn authentication verify failed')
            return Response({'error': str(e)}, status=400)
