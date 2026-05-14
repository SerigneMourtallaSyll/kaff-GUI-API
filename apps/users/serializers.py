"""Serializers du module Authentification (US-AUTH-01/02/03 + extension 2FA + crypto)."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.users.models import User
from apps.users.services import encryption


# ----------------------------------------------------------------------------
# Wrapper chiffré — input attendu de TOUS les endpoints prenant des credentials
# ----------------------------------------------------------------------------
class EncryptedPayloadSerializer(serializers.Serializer):
    """
    Le mobile envoie ``{"encrypted_payload": "<base64-sealed-box>"}``.

    On expose ``validated_payload`` (dict) après déchiffrement. Les sous-classes
    déclarent leurs propres règles de validation via ``inner_serializer_class``.
    """

    encrypted_payload = serializers.CharField(write_only=True, max_length=4096)

    inner_serializer_class: type[serializers.Serializer] | None = None

    def validate_encrypted_payload(self, value: str) -> dict[str, Any]:
        return encryption.decrypt_payload(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        payload = attrs["encrypted_payload"]  # déjà déchiffré → dict
        if self.inner_serializer_class is None:
            return {"payload": payload}

        inner = self.inner_serializer_class(data=payload)
        inner.is_valid(raise_exception=True)
        return {"payload": inner.validated_data}


# ----------------------------------------------------------------------------
# Inner schemas (validation du payload clair après déchiffrement)
# ----------------------------------------------------------------------------
class RegisterInnerSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, min_length=8, trim_whitespace=False)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)


class LoginInnerSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


# ----------------------------------------------------------------------------
# Serializers d'entrée pour les vues
# ----------------------------------------------------------------------------
class RegisterSerializer(EncryptedPayloadSerializer):
    inner_serializer_class = RegisterInnerSerializer


class LoginSerializer(EncryptedPayloadSerializer):
    inner_serializer_class = LoginInnerSerializer


class TOTPVerifySerializer(serializers.Serializer):
    """Étape 2 du login + confirmation d'enrôlement. Code 6 chiffres + challenge."""

    challenge_token = serializers.CharField(max_length=512)
    code = serializers.RegexField(regex=r"^\d{6}$", max_length=6, min_length=6)


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    """Représentation publique d'un utilisateur (pas de mot de passe, jamais)."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class LoginStep1ResponseSerializer(serializers.Serializer):
    state = serializers.CharField(default="TWO_FACTOR_REQUIRED")
    challenge_token = serializers.CharField()


class EnrollmentResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    challenge_token = serializers.CharField()
    provisioning_uri = serializers.CharField()
    qr_code_data_uri = serializers.CharField()


class AuthenticatedResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = TokenPairSerializer()


class PublicKeyResponseSerializer(serializers.Serializer):
    public_key = serializers.CharField()
    algorithm = serializers.CharField(default="x25519-sealed-box")


class LogoutSerializer(serializers.Serializer):
    """Body de POST /auth/logout/ — un refresh token à blacklist."""

    refresh = serializers.CharField()
