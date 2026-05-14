"""Manager pour le modèle User custom (email-based, pas de username)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from apps.users.models import User


class UserManager(BaseUserManager["User"]):
    """Crée des users à partir d'un email + mot de passe (US-AUTH-02)."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> User:
        if not email:
            raise ValueError("Un email est requis pour créer un utilisateur.")
        email = self.normalize_email(email).lower()  # email insensible à la casse (US-AUTH-01)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superuser doit avoir is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
