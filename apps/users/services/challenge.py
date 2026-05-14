"""
Challenge tokens — pont entre l'étape 1 (credentials vérifiés) et l'étape 2 (TOTP).

On utilise ``django.core.signing.TimestampSigner`` : pas de stockage côté serveur,
token signé HMAC, expiration courte (5 min). Stateless, scalable, robuste.
"""

from __future__ import annotations

from typing import Literal, cast

from django.conf import settings
from django.core import signing

ChallengeIntent = Literal["2fa", "enrollment"]


class InvalidChallengeError(Exception):
    """Token invalide, expiré, ou intent incorrect."""


def issue_challenge(user_id: str, intent: ChallengeIntent) -> str:
    """Crée un token signé pour un user + une intention donnée."""
    return signing.dumps(
        {"user_id": str(user_id), "intent": intent},
        salt=settings.AUTH_CHALLENGE_TOKEN_SALT,
    )


def consume_challenge(token: str, expected_intent: ChallengeIntent) -> str:
    """
    Valide un challenge token et renvoie l'user_id.

    Lève ``InvalidChallengeError`` si le token est expiré, mal signé ou ne
    correspond pas à l'intent attendu.
    """
    try:
        data = signing.loads(
            token,
            salt=settings.AUTH_CHALLENGE_TOKEN_SALT,
            max_age=settings.AUTH_CHALLENGE_TOKEN_TTL_SECONDS,
        )
    except signing.SignatureExpired as exc:
        raise InvalidChallengeError("Le challenge token a expiré.") from exc
    except signing.BadSignature as exc:
        raise InvalidChallengeError("Challenge token invalide.") from exc

    if not isinstance(data, dict):
        raise InvalidChallengeError("Challenge token mal formé.")
    if data.get("intent") != expected_intent:
        raise InvalidChallengeError("Challenge token utilisé pour un autre flow.")

    user_id = data.get("user_id")
    if not user_id or not isinstance(user_id, str):
        raise InvalidChallengeError("user_id manquant dans le challenge.")

    return cast("str", user_id)
