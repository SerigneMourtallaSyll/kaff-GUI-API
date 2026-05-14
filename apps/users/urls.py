"""URLs du module Authentification (US-AUTH-01/02/03 + 2FA TOTP + chiffrement applicatif)."""

from __future__ import annotations

from django.urls import path

from apps.users.views import (
    LoginView,
    LogoutView,
    MeView,
    PublicKeyView,
    RefreshView,
    RegisterConfirmView,
    RegisterView,
    TOTPVerifyView,
)

app_name = "users"

urlpatterns = [
    path("public-key/", PublicKeyView.as_view(), name="public-key"),
    path("register/", RegisterView.as_view(), name="register"),
    path("register/confirm/", RegisterConfirmView.as_view(), name="register-confirm"),
    path("login/", LoginView.as_view(), name="login"),
    path("2fa/verify/", TOTPVerifyView.as_view(), name="2fa-verify"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
