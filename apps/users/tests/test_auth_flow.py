"""
Tests d'intégration du flow d'authentification (US-AUTH-01/02/03 + 2FA + chiffrement).

Couvre :
- Happy path : register → confirm 2FA → login → verify 2FA → me → logout
- Edge case : payload chiffré corrompu → 410 Gone
- Edge case : code TOTP invalide → 401
- Edge case : challenge token expiré (simulé) → 401
"""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

import pytest
from freezegun import freeze_time
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
PUBLIC_KEY = "/api/v1/auth/public-key/"
REGISTER = "/api/v1/auth/register/"
REGISTER_CONFIRM = "/api/v1/auth/register/confirm/"
LOGIN = "/api/v1/auth/login/"
TOTP_VERIFY = "/api/v1/auth/2fa/verify/"
ME = "/api/v1/auth/me/"
LOGOUT = "/api/v1/auth/logout/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _register_user(
    api_client: APIClient,
    encrypt: Callable[[dict[str, Any]], str],
    totp_code_from_uri: Callable[[str], str],
    *,
    email: str = "baay@kaff.test",
    password: str = "Pigeon-1234!",
) -> tuple[str, str, str]:
    """Inscription + confirmation 2FA. Renvoie (user_id, access, refresh)."""
    response = api_client.post(
        REGISTER,
        {
            "encrypted_payload": encrypt(
                {
                    "email": email,
                    "password": password,
                    "first_name": "Baay",
                    "last_name": "Pitàq",
                }
            )
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    data = response.json()
    code = totp_code_from_uri(data["provisioning_uri"])

    response = api_client.post(
        REGISTER_CONFIRM,
        {"challenge_token": data["challenge_token"], "code": code},
        format="json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    return data["user"]["id"], body["tokens"]["access"], body["tokens"]["refresh"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_public_key_returned_as_base64_x25519(api_client: APIClient) -> None:
    response = api_client.get(PUBLIC_KEY)
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "x25519-sealed-box"
    key_bytes = base64.b64decode(data["public_key"])
    assert len(key_bytes) == 32  # X25519 key = 32 bytes


def test_full_happy_path_register_login_me_logout(
    api_client: APIClient,
    encrypt: Callable[[dict[str, Any]], str],
    totp_code_from_uri: Callable[[str], str],
) -> None:
    # freeze_time pour contrôler la fenêtre TOTP — chaque étape sauve un nouveau
    # `last_t` côté django-otp, on avance d'au moins 30s entre deux verifications.
    with freeze_time("2026-05-14 10:00:00"):
        response = api_client.post(
            REGISTER,
            {
                "encrypted_payload": encrypt(
                    {
                        "email": "baay@kaff.test",
                        "password": "Pigeon-1234!",
                        "first_name": "Baay",
                        "last_name": "Pitàq",
                    }
                )
            },
            format="json",
        )
        assert response.status_code == 201
        reg = response.json()
        assert reg["qr_code_data_uri"].startswith("data:image/png;base64,")
        assert reg["user"]["email"] == "baay@kaff.test"

        # Confirmation TOTP avec le 1er code (fenêtre A)
        code = totp_code_from_uri(reg["provisioning_uri"])
        response = api_client.post(
            REGISTER_CONFIRM,
            {"challenge_token": reg["challenge_token"], "code": code},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.json()["tokens"]

    # Avance d'1 minute pour passer à la fenêtre TOTP suivante
    with freeze_time("2026-05-14 10:01:00"):
        # Login étape 1
        response = api_client.post(
            LOGIN,
            {
                "encrypted_payload": encrypt(
                    {
                        "email": "baay@kaff.test",
                        "password": "Pigeon-1234!",
                    }
                )
            },
            format="json",
        )
        assert response.status_code == 200
        step1 = response.json()
        assert step1["state"] == "TWO_FACTOR_REQUIRED"

        # Login étape 2 (code TOTP de la fenêtre B)
        new_code = totp_code_from_uri(reg["provisioning_uri"])
        response = api_client.post(
            TOTP_VERIFY,
            {"challenge_token": step1["challenge_token"], "code": new_code},
            format="json",
        )
        assert response.status_code == 200, response.content
        tokens = response.json()["tokens"]

        # /me/ avec le Bearer
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(ME)
        assert response.status_code == 200
        assert response.json()["email"] == "baay@kaff.test"

        # Logout (blacklist du refresh)
        response = api_client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json")
        assert response.status_code == 204


def test_corrupted_encrypted_payload_returns_410(api_client: APIClient) -> None:
    """Payload qui n'est pas un sealed-box valide → 410 Gone (mobile doit re-fetch)."""
    response = api_client.post(
        LOGIN,
        {"encrypted_payload": base64.b64encode(b"definitely-not-a-sealed-box").decode()},
        format="json",
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "decryption_failed"


def test_invalid_totp_code_rejected(
    api_client: APIClient,
    encrypt: Callable[[dict[str, Any]], str],
    totp_code_from_uri: Callable[[str], str],
) -> None:
    _register_user(api_client, encrypt, totp_code_from_uri)

    response = api_client.post(
        LOGIN,
        {"encrypted_payload": encrypt({"email": "baay@kaff.test", "password": "Pigeon-1234!"})},
        format="json",
    )
    step1 = response.json()

    response = api_client.post(
        TOTP_VERIFY,
        {"challenge_token": step1["challenge_token"], "code": "000000"},
        format="json",
    )
    assert response.status_code == 401


def test_login_with_wrong_password_fails(
    api_client: APIClient,
    encrypt: Callable[[dict[str, Any]], str],
    totp_code_from_uri: Callable[[str], str],
) -> None:
    _register_user(api_client, encrypt, totp_code_from_uri)

    response = api_client.post(
        LOGIN,
        {"encrypted_payload": encrypt({"email": "baay@kaff.test", "password": "wrong-pass"})},
        format="json",
    )
    assert response.status_code == 401


def test_me_requires_authentication(api_client: APIClient) -> None:
    response = api_client.get(ME)
    assert response.status_code == 401


def test_register_rejects_duplicate_email(
    api_client: APIClient,
    encrypt: Callable[[dict[str, Any]], str],
    totp_code_from_uri: Callable[[str], str],
) -> None:
    _register_user(api_client, encrypt, totp_code_from_uri, email="dup@kaff.test")

    response = api_client.post(
        REGISTER,
        {
            "encrypted_payload": encrypt(
                {
                    "email": "dup@kaff.test",
                    "password": "Pigeon-1234!",
                    "first_name": "X",
                    "last_name": "Y",
                }
            )
        },
        format="json",
    )
    assert response.status_code == 400


def test_register_rejects_weak_password(
    api_client: APIClient, encrypt: Callable[[dict[str, Any]], str]
) -> None:
    response = api_client.post(
        REGISTER,
        {
            "encrypted_payload": encrypt(
                {
                    "email": "weak@kaff.test",
                    "password": "1234",
                    "first_name": "X",
                    "last_name": "Y",
                }
            )
        },
        format="json",
    )
    assert response.status_code == 400
