"""
Modèle User custom — email-based, UUID PK, pas de username.

Réf schéma DB § Table users.
Critique : AUTH_USER_MODEL doit pointer ici DÈS la première migration.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.models import TimeStampedModel, UUIDPrimaryKeyModel
from apps.users.managers import UserManager


class User(UUIDPrimaryKeyModel, TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur de l'application — un colombophile.

    L'authentification se fait par email (pas de username Django par défaut).
    """

    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name="Adresse email",
        help_text="Identifiant de connexion. Insensible à la casse.",
    )
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Désactive le compte sans suppression (RGPD-friendly).",
    )
    is_staff = models.BooleanField(default=False, verbose_name="Staff (accès admin)")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects: UserManager = UserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["email"], name="idx_users_email"),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.first_name
