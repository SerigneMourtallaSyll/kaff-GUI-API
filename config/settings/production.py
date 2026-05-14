"""Configuration de production — TLS strict, logs JSON, durcissement OWASP."""

from __future__ import annotations

from .base import *
from .base import LOGGING

DEBUG = False

# Retirer debug_toolbar si présent (sécurité)
INSTALLED_APPS = [
    app for app in INSTALLED_APPS if "debug_toolbar" not in app and "django_extensions" not in app
]
MIDDLEWARE = [mw for mw in MIDDLEWARE if "debug_toolbar" not in mw]

# Sécurité — durcissement complet
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logs JSON exclusivement
LOGGING = {
    **LOGGING,
    "root": {"handlers": ["json"], "level": "INFO"},
}

# Static files via WhiteNoise compressé
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
