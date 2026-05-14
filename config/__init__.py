"""Configuration du projet Kàff GUI."""

from __future__ import annotations

# Import de l'admin personnalisé pour qu'il soit chargé au démarrage
from config.admin import KaffAdminSite

__all__ = ["KaffAdminSite"]
