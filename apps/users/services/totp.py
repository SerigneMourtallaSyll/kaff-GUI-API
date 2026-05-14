"""
Service TOTP (2FA) — wrapper autour de django-otp.

Couvre :
- Enrôlement d'un nouveau device pour un user (non confirmé jusqu'à 1ère vérif).
- Génération du QR code (PNG base64 data-URI) pour l'app Authenticator.
- Vérification d'un code 6 chiffres.
- Lookup du device confirmé d'un user.
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

import qrcode
from django.conf import settings
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.common.exceptions import BusinessRuleError

if TYPE_CHECKING:
    from apps.users.models import User


class TOTPNotEnrolledError(BusinessRuleError):
    default_code = "totp_not_enrolled"
    default_detail = "L'utilisateur n'a pas terminé son enrôlement 2FA."


class TOTPVerificationError(BusinessRuleError):
    default_code = "totp_invalid_code"
    default_detail = "Code 2FA invalide ou expiré."


DEVICE_NAME = "default"


def get_or_create_unconfirmed_device(user: User) -> TOTPDevice:
    """
    Renvoie le device non confirmé du user, ou en crée un nouveau.

    Si l'utilisateur a déjà un device confirmé, on lève ``BusinessRuleError``
    pour éviter d'écraser un enrôlement valide.
    """
    if TOTPDevice.objects.filter(user=user, name=DEVICE_NAME, confirmed=True).exists():
        raise BusinessRuleError("2FA déjà enrôlé pour cet utilisateur.")

    device, _ = TOTPDevice.objects.get_or_create(
        user=user,
        name=DEVICE_NAME,
        defaults={"confirmed": False},
    )
    return device


def confirm_device(user: User, code: str) -> TOTPDevice:
    """
    Vérifie le premier code TOTP fourni et confirme le device.

    Doit être appelé après ``get_or_create_unconfirmed_device``.
    """
    try:
        device = TOTPDevice.objects.get(user=user, name=DEVICE_NAME, confirmed=False)
    except TOTPDevice.DoesNotExist as exc:
        raise TOTPNotEnrolledError(
            "Aucun device 2FA en cours d'enrôlement. Réinitialiser via /auth/register/."
        ) from exc

    if not device.verify_token(code):
        raise TOTPVerificationError()

    device.confirmed = True
    device.save(update_fields=["confirmed"])
    return device


def get_confirmed_device(user: User) -> TOTPDevice:
    """Renvoie le device 2FA confirmé du user, ou lève TOTPNotEnrolledError."""
    try:
        return TOTPDevice.objects.get(user=user, name=DEVICE_NAME, confirmed=True)
    except TOTPDevice.DoesNotExist as exc:
        raise TOTPNotEnrolledError() from exc


def verify_code(user: User, code: str) -> bool:
    """Vérifie un code TOTP pour l'utilisateur (device confirmé requis)."""
    device = get_confirmed_device(user)
    return bool(device.verify_token(code))


def build_provisioning_uri(device: TOTPDevice, user_email: str) -> str:
    """
    URI ``otpauth://`` pour configuration manuelle dans l'app Authenticator.

    Format : ``otpauth://totp/Kàff GUI:user@email?secret=...&issuer=Kàff%20GUI``
    """
    return str(device.config_url)


def build_qr_code_data_uri(provisioning_uri: str) -> str:
    """
    Génère un QR code PNG en base64 (data URI) à partir d'un URI de provisioning.

    Le mobile l'affiche directement avec ``<Image src="data:image/png;base64,..." />``.
    """
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def issuer() -> str:
    return getattr(settings, "OTP_TOTP_ISSUER", "Kàff GUI")
