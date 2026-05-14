"""
Endpoints d'authentification.

| Endpoint                       | Auth | Description                                           |
| ------------------------------ | ---- | ----------------------------------------------------- |
| GET  /auth/public-key/         | -    | Renvoie la clé publique X25519 (pour chiffrer creds). |
| POST /auth/register/           | -    | Étape 1 : crée le user + device TOTP non confirmé.    |
| POST /auth/register/confirm/   | -    | Étape 2 : confirme le 1er code TOTP → JWT.            |
| POST /auth/login/              | -    | Étape 1 : creds déchiffrés → challenge_token.          |
| POST /auth/2fa/verify/         | -    | Étape 2 : code TOTP → JWT.                            |
| POST /auth/logout/             | JWT  | Blacklist du refresh token (US-AUTH-03).               |
| POST /auth/refresh/            | -    | Renouvellement de l'access token.                     |
| GET  /auth/me/                 | JWT  | Profil de l'utilisateur courant.                      |
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

if TYPE_CHECKING:
    from rest_framework.request import Request

from apps.users.serializers import (
    AuthenticatedResponseSerializer,
    EnrollmentResponseSerializer,
    LoginSerializer,
    LoginStep1ResponseSerializer,
    LogoutSerializer,
    PublicKeyResponseSerializer,
    RegisterSerializer,
    TOTPVerifySerializer,
    UserSerializer,
)
from apps.users.services import auth_flow
from apps.users.services.keypair import get_app_keypair


# ----------------------------------------------------------------------------
# 1. Clé publique X25519 — première requête du mobile au boot
# ----------------------------------------------------------------------------
class PublicKeyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_key"

    @extend_schema(
        operation_id="auth_public_key",
        tags=["auth"],
        responses=PublicKeyResponseSerializer,
        description=(
            "Renvoie la clé publique X25519 utilisée pour chiffrer les credentials "
            "via libsodium sealed box. Le mobile doit re-fetcher si une requête de "
            "login/register échoue en 410 Gone."
        ),
    )
    def get(self, request: Request) -> Response:
        keypair = get_app_keypair()
        return Response({"public_key": keypair.public_key_b64, "algorithm": "x25519-sealed-box"})


# ----------------------------------------------------------------------------
# 2. Register (étape 1) — crée user + device TOTP non confirmé + QR code
# ----------------------------------------------------------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    @extend_schema(
        operation_id="auth_register",
        tags=["auth"],
        request=RegisterSerializer,
        responses={201: EnrollmentResponseSerializer},
        description=(
            "Étape 1 d'inscription. Reçoit `encrypted_payload` (sealed box base64) "
            "contenant {email, password, first_name, last_name}. Crée le user et "
            "renvoie le QR code à scanner dans l'app Authenticator + un "
            "`challenge_token` à utiliser dans `/auth/register/confirm/`."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload: dict[str, Any] = serializer.validated_data["payload"]

        user, artifact = auth_flow.register(
            email=payload["email"],
            password=payload["password"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
        )

        response_data = {
            "user": UserSerializer(user).data,
            "challenge_token": artifact.challenge_token,
            "provisioning_uri": artifact.provisioning_uri,
            "qr_code_data_uri": artifact.qr_code_data_uri,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------------------------------
# 3. Register confirm (étape 2) — premier code TOTP → JWT
# ----------------------------------------------------------------------------
class RegisterConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "totp_verify"

    @extend_schema(
        operation_id="auth_register_confirm",
        tags=["auth"],
        request=TOTPVerifySerializer,
        responses={200: AuthenticatedResponseSerializer},
        description=(
            "Confirme l'enrôlement 2FA en validant le 1er code généré par "
            "l'Authenticator. Émet les tokens JWT — l'utilisateur est désormais "
            "authentifié."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = TOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        challenge_token = serializer.validated_data["challenge_token"]
        code = serializer.validated_data["code"]

        user, tokens = auth_flow.confirm_registration(challenge_token=challenge_token, code=code)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {"access": tokens.access, "refresh": tokens.refresh},
            }
        )


# ----------------------------------------------------------------------------
# 4. Login étape 1 — credentials → challenge_token
# ----------------------------------------------------------------------------
class LoginThrottle(AnonRateThrottle):
    scope = "login"


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        operation_id="auth_login",
        tags=["auth"],
        request=LoginSerializer,
        responses={200: LoginStep1ResponseSerializer},
        description=(
            "Étape 1 du login. Reçoit `encrypted_payload` (sealed box) contenant "
            "{email, password}. Valide les credentials, déclenche django-axes "
            "(5 échecs/5min = lockout). Renvoie un `challenge_token` à utiliser "
            "dans `/auth/2fa/verify/` avec le code TOTP."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload: dict[str, Any] = serializer.validated_data["payload"]

        _, result = auth_flow.login_step1(
            email=payload["email"], password=payload["password"], request=request
        )
        return Response({"state": "TWO_FACTOR_REQUIRED", "challenge_token": result.challenge_token})


# ----------------------------------------------------------------------------
# 5. Login étape 2 — code TOTP → JWT
# ----------------------------------------------------------------------------
class TOTPVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "totp_verify"

    @extend_schema(
        operation_id="auth_login_2fa",
        tags=["auth"],
        request=TOTPVerifySerializer,
        responses={200: AuthenticatedResponseSerializer},
        description=(
            "Étape 2 du login. Reçoit le `challenge_token` (émis par /auth/login/) "
            "et le code 6 chiffres de l'Authenticator. Émet les tokens JWT."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = TOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        challenge_token = serializer.validated_data["challenge_token"]
        code = serializer.validated_data["code"]

        user, tokens = auth_flow.login_step2(challenge_token=challenge_token, code=code)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {"access": tokens.access, "refresh": tokens.refresh},
            }
        )


# ----------------------------------------------------------------------------
# 6. Logout — blacklist du refresh (US-AUTH-03)
# ----------------------------------------------------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="auth_logout",
        tags=["auth"],
        request=LogoutSerializer,
        responses={204: None},
        description="Blackliste le refresh token fourni (US-AUTH-03).",
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------------
# 7. Refresh — renouvellement de l'access token (simplejwt fait le job)
# ----------------------------------------------------------------------------
class RefreshView(TokenRefreshView):
    """Wrap pour préciser les tags Swagger."""

    @extend_schema(
        operation_id="auth_refresh",
        tags=["auth"],
        description="Échange un refresh token contre un nouvel access (+ rotation).",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)


# ----------------------------------------------------------------------------
# 8. Me — profil courant
# ----------------------------------------------------------------------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="auth_me",
        tags=["auth"],
        responses=UserSerializer,
        description="Retourne le profil de l'utilisateur authentifié.",
    )
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)
