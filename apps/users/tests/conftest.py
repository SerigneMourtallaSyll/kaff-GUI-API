"""Fixtures et helpers pour les tests d'authentification."""

from __future__ import annotations

import base64
import json
from collections.abc import Callable
from typing import Any

import pyotp
import pytest
from nacl.public import PublicKey, SealedBox
from rest_framework.test import APIClient


def seal_payload(payload: dict[str, Any], server_public_key_b64: str) -> str:
    """
    Reproduit côté tests le chiffrement effectué par le mobile.

    Renvoie un base64 prêt à mettre dans ``encrypted_payload``.
    """
    pk = PublicKey(base64.b64decode(server_public_key_b64))
    ct = SealedBox(pk).encrypt(json.dumps(payload).encode("utf-8"))
    return base64.b64encode(ct).decode("ascii")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def server_public_key(api_client: APIClient) -> str:
    """Récupère la clé publique via l'endpoint pour utilisation dans les tests."""
    response = api_client.get("/api/v1/auth/public-key/")
    assert response.status_code == 200, response.content
    return str(response.json()["public_key"])


@pytest.fixture
def encrypt(server_public_key: str) -> Callable[[dict[str, Any]], str]:
    """Helper : reçoit un dict, renvoie son sealed-box base64."""

    def _encrypt(payload: dict[str, Any]) -> str:
        return seal_payload(payload, server_public_key)

    return _encrypt


@pytest.fixture
def totp_code_from_uri() -> Callable[[str], str]:
    """Helper : extrait le secret d'un otpauth:// URI et renvoie le code courant."""

    def _code(provisioning_uri: str) -> str:
        totp = pyotp.parse_uri(provisioning_uri)
        return totp.now()

    return _code
