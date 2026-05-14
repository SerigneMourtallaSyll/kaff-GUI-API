"""
Gestion du keypair X25519 utilisé pour le chiffrement applicatif des credentials.

- En production : les clés DOIVENT être fournies via les variables d'environnement
  ``APP_CRYPTO_PRIVATE_KEY`` et ``APP_CRYPTO_PUBLIC_KEY`` (base64).
- En développement : si non définies, on génère un keypair éphémère au boot du
  process. Le mobile re-fetch la clé publique sur erreur de déchiffrement.

Rotation : opérationnelle (redéploiement). Pas de rotation programmée en MVP.
"""

from __future__ import annotations

import base64
import threading
from dataclasses import dataclass

import structlog
from django.conf import settings
from nacl.public import PrivateKey, PublicKey

logger = structlog.get_logger(__name__)

_LOCK = threading.Lock()
_CACHED: KeyPair | None = None


@dataclass(frozen=True)
class KeyPair:
    """Encapsule un keypair X25519 chargé en mémoire."""

    private_key: PrivateKey
    public_key: PublicKey

    @property
    def public_key_b64(self) -> str:
        return base64.b64encode(bytes(self.public_key)).decode("ascii")

    @property
    def private_key_b64(self) -> str:
        return base64.b64encode(bytes(self.private_key)).decode("ascii")


def get_app_keypair() -> KeyPair:
    """
    Renvoie le keypair courant. Charge depuis les settings ou génère à la volée.

    Thread-safe : un seul keypair par process, mémoïsé.
    """
    global _CACHED
    if _CACHED is not None:
        return _CACHED

    with _LOCK:
        if _CACHED is not None:
            return _CACHED

        priv_b64 = settings.APP_CRYPTO_PRIVATE_KEY
        pub_b64 = settings.APP_CRYPTO_PUBLIC_KEY

        if priv_b64 and pub_b64:
            try:
                private_key = PrivateKey(base64.b64decode(priv_b64))
                public_key = PublicKey(base64.b64decode(pub_b64))
            except Exception as exc:
                raise RuntimeError(
                    "APP_CRYPTO_PRIVATE_KEY / APP_CRYPTO_PUBLIC_KEY invalides "
                    "(base64 attendu, 32 octets après décodage)."
                ) from exc
            _CACHED = KeyPair(private_key=private_key, public_key=public_key)
            logger.info("app_keypair.loaded_from_env")
        else:
            allow_ephemeral = settings.DEBUG or getattr(settings, "TESTING", False)
            if not allow_ephemeral:
                raise RuntimeError(
                    "APP_CRYPTO_PRIVATE_KEY / APP_CRYPTO_PUBLIC_KEY doivent être "
                    "définies en production. Générer avec `manage.py shell` :\n"
                    "  from apps.users.services.keypair import generate_pair\n"
                    "  generate_pair()"
                )
            ephemeral = PrivateKey.generate()
            _CACHED = KeyPair(private_key=ephemeral, public_key=ephemeral.public_key)
            logger.warning(
                "app_keypair.generated_ephemeral",
                hint="Définir APP_CRYPTO_* en .env pour stabiliser le keypair.",
            )

        return _CACHED


def generate_pair() -> tuple[str, str]:
    """
    Génère un nouveau keypair X25519 et imprime les valeurs base64 à coller dans .env.

    Usage : ``uv run python manage.py shell -c "from apps.users.services.keypair import generate_pair; generate_pair()"``
    """
    sk = PrivateKey.generate()
    priv_b64 = base64.b64encode(bytes(sk)).decode("ascii")
    pub_b64 = base64.b64encode(bytes(sk.public_key)).decode("ascii")
    print(f"APP_CRYPTO_PRIVATE_KEY={priv_b64}")
    print(f"APP_CRYPTO_PUBLIC_KEY={pub_b64}")
    return priv_b64, pub_b64


def reset_cache_for_testing() -> None:
    """À utiliser uniquement dans les tests pour forcer un re-chargement."""
    global _CACHED
    with _LOCK:
        _CACHED = None
