"""Configuration de développement local — verbeuse, permissive, instrumentée."""

from __future__ import annotations

from .base import *
from .base import INSTALLED_APPS, MIDDLEWARE, REST_FRAMEWORK

DEBUG = True

# Sécurité relâchée en local (jamais en prod)
ALLOWED_HOSTS = ["*"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS large en dev pour l'app Expo
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar", "django_extensions"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Throttling permissif en dev (DRF refuse de muter le dict importé)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/min",
        "user": "10000/min",
        "login": "100/min",
    },
}
