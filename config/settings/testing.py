"""Configuration de test — rapide, déterministe, hashers triviaux."""

from __future__ import annotations

from .base import *

DEBUG = False
TESTING = True

# Hasher rapide pour ne pas ralentir les tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Désactiver axes pour les tests d'auth qui simulent des échecs
AXES_ENABLED = False

# Email backend en mémoire
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Logs silencieux
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}

# Pas d'atomic_requests en test — chaque test gère ses transactions
DATABASES["default"]["ATOMIC_REQUESTS"] = False
