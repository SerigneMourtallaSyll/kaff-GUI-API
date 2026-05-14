"""
Configuration Django commune à tous les environnements.

Conventions :
- Aucune valeur secrète n'est hard-codée. Tout passe par django-environ → .env.
- Les overrides par environnement vivent dans development.py / production.py / testing.py.
- L'ordre des middlewares respecte les exigences DRF, CORS, Axes et WhiteNoise.

Réfs :
- Cahier des charges Kàff-GUI §5 (OWASP Top 10).
- User stories US-AUTH-* (JWT 15 min / 7 j, blacklist).
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import environ
import structlog

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Environment loading (django-environ)
# ---------------------------------------------------------------------------
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DATABASE_CONN_MAX_AGE=(int, 60),
    DATABASE_SSL_REQUIRE=(bool, False),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    JWT_ROTATE_REFRESH_TOKENS=(bool, True),
    JWT_BLACKLIST_AFTER_ROTATION=(bool, True),
    AXES_FAILURE_LIMIT=(int, 5),
    AXES_COOLOFF_TIME_MINUTES=(int, 5),
)

# Lire le fichier .env s'il existe (silencieux en CI / prod où les vars sont injectées)
env_file = BASE_DIR / ".env"
if env_file.is_file():
    env.read_env(str(env_file))

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "axes",
    "django_structlog",
    # 2FA TOTP (RFC 6238)
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",  # codes de récupération
]

LOCAL_APPS = [
    "apps.common",
    "apps.users",
    "apps.pigeons",
    "apps.cages",
    "apps.couples",
    "apps.reproductions",
    "apps.sorties",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware (ordre important)
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # static files en prod
    "corsheaders.middleware.CorsMiddleware",  # CORS avant CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",  # APRÈS auth, AVANT toutes les vues
    "django_structlog.middlewares.RequestMiddleware",  # logs structurés request_id
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # DOIT être en dernier
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Templates (utilisé par l'admin uniquement)
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database (PostgreSQL 15 via psycopg 3)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "CONN_MAX_AGE": env("DATABASE_CONN_MAX_AGE"),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            # SSL pour la prod (Railway/Render). Désactivé en local.
            **({"sslmode": "require"} if env("DATABASE_SSL_REQUIRE") else {}),
        },
        "ATOMIC_REQUESTS": True,  # chaque vue = une transaction (intégrité métier)
    }
}

# Forcer le driver psycopg 3
DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Auth — Custom user model dès le départ (obligatoire pour ne pas se peindre dans un coin)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},  # US-AUTH-02
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Hashers — Argon2 en tête (recommandé OWASP), PBKDF2 en fallback Django legacy
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # DOIT être en premier (anti-bruteforce)
    "django.contrib.auth.backends.ModelBackend",
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="fr")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="Africa/Dakar")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / Media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS: list[Path] = []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",  # OWASP A01 — secure by default
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.DefaultPageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",  # uploads photo pigeon
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        "login": "10/min",  # POST /auth/login
        "totp_verify": "10/min",  # POST /auth/2fa/verify
        "register": "5/min",  # POST /auth/register
        "public_key": "30/min",  # GET  /auth/public-key
    },
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# ---------------------------------------------------------------------------
# Simple JWT — US-AUTH-01/03
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS")),
    "ROTATE_REFRESH_TOKENS": env("JWT_ROTATE_REFRESH_TOKENS"),
    "BLACKLIST_AFTER_ROTATION": env("JWT_BLACKLIST_AFTER_ROTATION"),
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_TYPE_CLAIM": "token_type",  # nosec B105 — nom de claim JWT, pas un secret
    "JTI_CLAIM": "jti",
}

# ---------------------------------------------------------------------------
# drf-spectacular (OpenAPI 3)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Kàff GUI API",
    "DESCRIPTION": (
        "API REST de gestion de volière colombophile.\n\n"
        "## Authentification\n\n"
        "L'API utilise JWT (JSON Web Tokens) avec authentification 2FA (TOTP).\n\n"
        "### Flux d'authentification\n\n"
        "1. **Inscription** : `POST /api/v1/auth/register/` - Retourne un QR code TOTP\n"
        "2. **Confirmation TOTP** : `POST /api/v1/auth/2fa/confirm/` - Active le compte\n"
        "3. **Connexion** : `POST /api/v1/auth/login/` - Retourne access + refresh tokens\n"
        "4. **Utilisation** : Ajouter `Authorization: Bearer <access_token>` dans les headers\n"
        "5. **Refresh** : `POST /api/v1/auth/token/refresh/` - Obtenir un nouveau access token\n\n"
        "### Sécurité\n\n"
        "- Tokens access : 15 minutes de validité\n"
        "- Tokens refresh : 7 jours de validité avec rotation\n"
        "- Rate limiting : 300 req/min pour utilisateurs authentifiés\n"
        "- Protection brute-force : 5 tentatives max, cooldown 5 min\n\n"
        "Voir le cahier des charges et les user stories pour le détail métier."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+/",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
    "SECURITY": [{"Bearer": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT access token obtenu via /api/v1/auth/login/",
            }
        }
    },
    "TAGS": [
        {"name": "auth", "description": "Authentification JWT + 2FA (TOTP)"},
        {"name": "dashboard", "description": "KPIs et statistiques agrégées"},
        {"name": "pigeons", "description": "Gestion des pigeons et généalogie"},
        {"name": "cages", "description": "Cages et occupations"},
        {"name": "couples", "description": "Formation et dissolution des couples"},
        {"name": "reproductions", "description": "Reproductions et pigeonneaux"},
        {"name": "sorties", "description": "Sorties (vente/décès/perte)"},
    ],
    "CONTACT": {
        "name": "Serigne Mourtalla Syll",
        "email": "serignemourtallasyll86@gmail.com",
    },
    "LICENSE": {
        "name": "Proprietary",
    },
    "EXTERNAL_DOCS": {
        "description": "Documentation complète du projet",
        "url": "https://github.com/SerigneMourtallaSyll/kaff-GUI-API",
    },
}

# ---------------------------------------------------------------------------
# CORS — restreint à la liste explicite (jamais "*")
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]

# ---------------------------------------------------------------------------
# Axes — brute-force protection (US-AUTH-01)
# ---------------------------------------------------------------------------
AXES_FAILURE_LIMIT = env("AXES_FAILURE_LIMIT")
AXES_COOLOFF_TIME = timedelta(minutes=env("AXES_COOLOFF_TIME_MINUTES"))
AXES_LOCKOUT_PARAMETERS = env.list("AXES_LOCKOUT_PARAMETERS", default=["ip_address", "username"])
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = True
AXES_USERNAME_FORM_FIELD = "email"

# ---------------------------------------------------------------------------
# Logging — structuré JSON pour la prod, console lisible en dev
# ---------------------------------------------------------------------------
LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")

# Pré-chain appliquée aux logs venant du stdlib logging (Django, axes, etc.),
# pour les harmoniser avec ceux émis directement par structlog.
_LOGGING_PRE_CHAIN = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": _LOGGING_PRE_CHAIN,
        },
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "foreign_pre_chain": _LOGGING_PRE_CHAIN,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django_structlog": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "axes": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

# Configuration structlog (loggers natifs structlog, hors stdlib)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# ---------------------------------------------------------------------------
# Chiffrement applicatif des credentials (X25519 sealed box via PyNaCl)
# ---------------------------------------------------------------------------
# Clés en base64 (44 caractères) — générées via:
#   uv run python -c "from nacl.public import PrivateKey; import base64
#   sk = PrivateKey.generate(); print('PRIV=', base64.b64encode(bytes(sk)).decode())
#   print('PUB=', base64.b64encode(bytes(sk.public_key)).decode())"
# Si non définies, generated_keypair() en dev (rotation à chaque restart) — voir
# apps.users.services.keypair.
APP_CRYPTO_PRIVATE_KEY = env("APP_CRYPTO_PRIVATE_KEY", default="")
APP_CRYPTO_PUBLIC_KEY = env("APP_CRYPTO_PUBLIC_KEY", default="")

# ---------------------------------------------------------------------------
# Challenge token (étape 1 → 2 du login 2FA) — Django signing
# ---------------------------------------------------------------------------
AUTH_CHALLENGE_TOKEN_TTL_SECONDS = 300  # 5 min
# Salt public — sert à isoler le domaine de signing, pas un secret (cf. Django docs).
AUTH_CHALLENGE_TOKEN_SALT = "kaff.auth.challenge.v1"  # nosec B105

# ---------------------------------------------------------------------------
# django-otp — TOTP
# ---------------------------------------------------------------------------
OTP_TOTP_ISSUER = "Kàff GUI"

# ---------------------------------------------------------------------------
# Sécurité — défaut sain, durci en production.py (OWASP § 5)
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Surchargé dans production.py
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)
