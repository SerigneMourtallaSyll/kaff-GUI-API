"""
Déchiffrement applicatif des payloads venant du mobile.

Protocole : libsodium **sealed box** (X25519 + XSalsa20-Poly1305).

Côté mobile (React Native) :
    import { box, BoxKeyPair } from 'tweetnacl';
    const ephemeral = box.keyPair();                // éphémère
    const ciphertext = box(
        utf8Encode(JSON.stringify(payload)),
        nonce, serverPublicKey, ephemeral.secretKey
    );
    // ou plus simple, sealedbox_easy (libsodium-rn) :
    const sealed = sealedbox_easy(message, serverPublicKey);
    // → envoyé en base64 dans `encrypted_payload`

Côté backend (ici) : on décode le base64 puis `SealedBox.decrypt`.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import structlog
from nacl.exceptions import CryptoError
from nacl.public import SealedBox

from apps.common.exceptions import BusinessRuleError
from apps.users.services.keypair import get_app_keypair

logger = structlog.get_logger(__name__)

# Limite de taille pour éviter les attaques DoS (payload max attendu : ~200 octets)
MAX_ENCRYPTED_PAYLOAD_BYTES = 4096


class DecryptionError(BusinessRuleError):
    """Le déchiffrement a échoué (payload corrompu, mauvaise clé, expiré)."""

    default_code = "decryption_failed"
    default_detail = (
        "Impossible de déchiffrer le payload. Vérifier que la clé publique utilisée "
        "est à jour (GET /api/v1/auth/public-key/)."
    )
    status_code: int = 410  # 410 Gone — signale au mobile de re-fetch la clé publique


def decrypt_payload(encrypted_b64: str) -> dict[str, Any]:
    """
    Déchiffre un sealed-box base64 et renvoie le payload JSON.

    Lève ``DecryptionError`` (HTTP 410) si :
    - le base64 est invalide,
    - le ciphertext est rejeté par libsodium (clé invalide, payload corrompu),
    - le JSON déchiffré est mal formé,
    - la taille dépasse ``MAX_ENCRYPTED_PAYLOAD_BYTES``.
    """
    if not encrypted_b64 or not isinstance(encrypted_b64, str):
        raise DecryptionError("encrypted_payload manquant ou invalide.")

    if len(encrypted_b64) > MAX_ENCRYPTED_PAYLOAD_BYTES:
        logger.warning("decrypt.payload_too_large", size=len(encrypted_b64))
        raise DecryptionError("Payload trop volumineux.")

    try:
        ciphertext = base64.b64decode(encrypted_b64, validate=True)
    except (ValueError, TypeError) as exc:
        raise DecryptionError("encrypted_payload n'est pas du base64 valide.") from exc

    keypair = get_app_keypair()
    sealed = SealedBox(keypair.private_key)

    try:
        plaintext = sealed.decrypt(ciphertext)
    except CryptoError as exc:
        # NE PAS logger le payload (peut contenir des credentials s'il est partiellement déchiffré)
        logger.warning("decrypt.crypto_error", reason=str(exc))
        raise DecryptionError() from exc

    try:
        data = json.loads(plaintext.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("decrypt.json_error")
        raise DecryptionError("Payload déchiffré non JSON.") from exc

    if not isinstance(data, dict):
        raise DecryptionError("Payload déchiffré n'est pas un objet JSON.")

    return data
