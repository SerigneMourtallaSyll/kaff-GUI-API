"""Configuration de test — rapide, déterministe, hashers triviaux."""

from __future__ import annotations

from .base import *
from .base import MIDDLEWARE, REST_FRAMEWORK

DEBUG = False
TESTING = True

# Retirer whitenoise (statics prod) — évite "No directory at: staticfiles/" promu en error
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m.lower()]

# Hasher rapide pour ne pas ralentir les tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Throttles très élevés pour les tests — les vues conservent leurs throttle_classes
# (ScopedRateThrottle, LoginThrottle) mais les rates ne saturent jamais.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100000/min",
        "user": "100000/min",
        "login": "100000/min",
        "totp_verify": "100000/min",
        "register": "100000/min",
        "public_key": "100000/min",
    },
}

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
