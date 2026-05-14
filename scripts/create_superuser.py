#!/usr/bin/env python
"""
Script pour créer un superuser en production (Railway).

Usage:
    python scripts/create_superuser.py

Variables d'environnement requises:
    SUPERUSER_EMAIL (défaut: admin@kaffgui.com)
    SUPERUSER_PASSWORD (défaut: ChangeMe123!)
    SUPERUSER_FIRST_NAME (défaut: Admin)
    SUPERUSER_LAST_NAME (défaut: Kàff GUI)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import django  # noqa: E402

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from apps.users.models import User  # noqa: E402


def create_superuser() -> None:
    """Crée un superuser si il n'existe pas déjà."""
    email = os.getenv("SUPERUSER_EMAIL", "admin@kaffgui.com")
    password = os.getenv("SUPERUSER_PASSWORD", "ChangeMe123!")
    first_name = os.getenv("SUPERUSER_FIRST_NAME", "Admin")
    last_name = os.getenv("SUPERUSER_LAST_NAME", "Kàff GUI")

    if User.objects.filter(email=email).exists():
        print(f"Info: Superuser avec l'email '{email}' existe déjà.")
        sys.exit(0)

    try:
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        print("✅ Superuser créé avec succès !")
        print(f"   Email: {user.email}")
        print(f"   Nom: {user.get_full_name()}")
        print("\n⚠️  IMPORTANT: Changez le mot de passe immédiatement via /admin/")
    except Exception as e:
        print(f"❌ Erreur lors de la création du superuser: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_superuser()
