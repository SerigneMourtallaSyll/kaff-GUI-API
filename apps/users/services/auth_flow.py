"""
Orchestration du flow d'authentification 2FA chiffré.

Étapes :
    1. ``register`` — créer un user + un device TOTP non confirmé + QR code.
    2. ``confirm_registration`` — première vérification du code → device confirmé +
       JWT access/refresh émis.
    3. ``login_step1`` — vérifier credentials (déchiffrés). Si OK, renvoyer un
       challenge token signé pour passer à l'étape 2.
    4. ``login_step2`` — valider le code TOTP avec le challenge token. Si OK,
       émettre les tokens JWT.

Tous les checks de rate-limit (django-axes) sont déclenchés côté view via
``axes.helpers.get_client_username`` ; la logique métier ne s'en préoccupe pas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.services import challenge, totp

logger = structlog.get_logger(__name__)


# ----------------------------------------------------------------------------
# DTOs
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str


@dataclass(frozen=True)
class EnrollmentArtifact:
    """À renvoyer au mobile pour scanner le QR (étape 1 de l'inscription)."""

    challenge_token: str  # à renvoyer avec le code TOTP pour confirmer
    provisioning_uri: str
    qr_code_data_uri: str


@dataclass(frozen=True)
class LoginStep1Result:
    challenge_token: str  # à renvoyer avec le code TOTP pour l'étape 2


# ----------------------------------------------------------------------------
# Issuance JWT
# ----------------------------------------------------------------------------
def issue_tokens(user: User) -> TokenPair:
    refresh = RefreshToken.for_user(user)
    return TokenPair(access=str(refresh.access_token), refresh=str(refresh))


# ----------------------------------------------------------------------------
# Registration (US-AUTH-02 — étendu par exigence 2FA obligatoire)
# ----------------------------------------------------------------------------
@transaction.atomic
def register(
    *, email: str, password: str, first_name: str, last_name: str
) -> tuple[User, EnrollmentArtifact]:
    """
    Crée un user + un device TOTP non confirmé + renvoie le QR code à afficher.

    L'utilisateur n'est PAS encore authentifiable tant que le code n'a pas été
    confirmé via ``confirm_registration``.
    """
    email_normalized = email.strip().lower()
    if not email_normalized:
        raise ValidationError({"email": "Email requis."})

    if User.objects.filter(email=email_normalized).exists():
        raise ValidationError({"email": "Cet email est déjà utilisé."})

    # Validation mot de passe (validateurs Django configurés dans settings)
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise ValidationError({"password": list(exc.messages)}) from exc

    user = User.objects.create_user(
        email=email_normalized,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        is_active=True,
    )

    device = totp.get_or_create_unconfirmed_device(user)
    uri = totp.build_provisioning_uri(device, user.email)

    artifact = EnrollmentArtifact(
        challenge_token=challenge.issue_challenge(str(user.id), intent="enrollment"),
        provisioning_uri=uri,
        qr_code_data_uri=totp.build_qr_code_data_uri(uri),
    )

    logger.info("auth.register.created", user_id=str(user.id))
    return user, artifact


def confirm_registration(*, challenge_token: str, code: str) -> tuple[User, TokenPair]:
    """
    Confirme le device TOTP via le 1er code généré, et émet les tokens.

    Doit être appelé dans les 5 minutes suivant ``register``.
    """
    try:
        user_id = challenge.consume_challenge(challenge_token, expected_intent="enrollment")
    except challenge.InvalidChallengeError as exc:
        raise AuthenticationFailed(str(exc)) from exc

    user = _get_active_user(user_id)
    totp.confirm_device(user, code)

    tokens = issue_tokens(user)
    logger.info("auth.register.confirmed", user_id=str(user.id))
    return user, tokens


# ----------------------------------------------------------------------------
# Login en 2 étapes (US-AUTH-01 — étendu par 2FA)
# ----------------------------------------------------------------------------
def login_step1(*, email: str, password: str, request: Any) -> tuple[User, LoginStep1Result]:
    """
    Vérifie les credentials. Si OK, renvoie un challenge token pour l'étape 2 (TOTP).

    Le ``request`` est passé à ``authenticate()`` pour permettre à django-axes de
    tracer les tentatives (verrouillage IP / username sur 5 échecs en 5 min).
    """
    email_normalized = email.strip().lower()

    user = authenticate(request=request, username=email_normalized, password=password)
    if user is None or not isinstance(user, User):
        raise AuthenticationFailed("Identifiants invalides ou compte verrouillé.")

    if not user.is_active:
        raise AuthenticationFailed("Compte désactivé.")

    # Exiger qu'un TOTP soit déjà confirmé — sinon, on bloque ici
    totp.get_confirmed_device(user)  # lève TOTPNotEnrolledError si absent

    token = challenge.issue_challenge(str(user.id), intent="2fa")
    logger.info("auth.login.step1.ok", user_id=str(user.id))
    return user, LoginStep1Result(challenge_token=token)


def login_step2(*, challenge_token: str, code: str) -> tuple[User, TokenPair]:
    """Valide le code TOTP avec le challenge token et émet les tokens."""
    try:
        user_id = challenge.consume_challenge(challenge_token, expected_intent="2fa")
    except challenge.InvalidChallengeError as exc:
        raise AuthenticationFailed(str(exc)) from exc

    user = _get_active_user(user_id)

    if not totp.verify_code(user, code):
        logger.warning("auth.login.step2.totp_failed", user_id=str(user.id))
        raise AuthenticationFailed("Code 2FA invalide.")

    tokens = issue_tokens(user)
    logger.info("auth.login.step2.ok", user_id=str(user.id))
    return user, tokens


# ----------------------------------------------------------------------------
# Internes
# ----------------------------------------------------------------------------
def _get_active_user(user_id: str) -> User:
    try:
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError) as exc:
        raise AuthenticationFailed("Utilisateur introuvable.") from exc

    if not user.is_active:
        raise AuthenticationFailed("Compte désactivé.")
    return user
