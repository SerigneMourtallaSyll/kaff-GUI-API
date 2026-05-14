#!/usr/bin/env python
"""
Script pour générer les secrets nécessaires au déploiement Railway.

Usage:
    python scripts/generate_secrets.py
"""

from __future__ import annotations

import base64

from django.core.management.utils import get_random_secret_key
from nacl.public import PrivateKey


def generate_django_secret_key() -> str:
    """Génère une SECRET_KEY Django sécurisée."""
    return get_random_secret_key()


def generate_nacl_keypair() -> tuple[str, str]:
    """Génère une paire de clés NaCl (X25519) pour le chiffrement des credentials."""
    private_key = PrivateKey.generate()
    private_key_b64 = base64.b64encode(bytes(private_key)).decode()
    public_key_b64 = base64.b64encode(bytes(private_key.public_key)).decode()
    return private_key_b64, public_key_b64


def main() -> None:
    """Point d'entrée principal."""
    print("🔐 Génération des secrets pour Railway\n")
    print("=" * 80)

    # Django SECRET_KEY
    django_secret = generate_django_secret_key()
    print("\n📌 Django SECRET_KEY:")
    print(f"DJANGO_SECRET_KEY={django_secret}")

    # NaCl keypair
    private_key, public_key = generate_nacl_keypair()
    print("\n📌 NaCl Keypair (chiffrement credentials):")
    print(f"APP_CRYPTO_PRIVATE_KEY={private_key}")
    print(f"APP_CRYPTO_PUBLIC_KEY={public_key}")

    print("\n" + "=" * 80)
    print("\n✅ Secrets générés avec succès !")
    print("\n📋 Copiez ces valeurs dans les variables d'environnement Railway.")
    print("⚠️  Ne commitez JAMAIS ces secrets dans Git !")


if __name__ == "__main__":
    main()
