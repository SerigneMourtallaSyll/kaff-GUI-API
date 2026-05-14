"""
Modèles abstraits réutilisables.

- ``UUIDPrimaryKeyModel`` — PK UUID v4 (gen_random_uuid côté PG).
- ``TimeStampedModel`` — created_at / updated_at automatiques.
- ``SoftDeleteModel`` — deleted_at + manager qui exclut les soft-deleted par défaut.
- ``BaseModel`` — combo des trois (UUID + timestamps + soft delete optionnel via mixin).

Réf schéma : table pigeons → soft delete ; toutes les tables → PK UUID + timestamps.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, ClassVar

from django.db import models
from django.utils import timezone

from apps.common.managers import ActiveManager, SoftDeleteManager

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class UUIDPrimaryKeyModel(models.Model):
    """Active une PK UUID v4 (compatible gen_random_uuid en PostgreSQL)."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant",
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Ajoute created_at et updated_at, gérés par Django (auto_now_add / auto_now)."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Soft delete via ``deleted_at``.

    - ``objects`` exclut les enregistrements supprimés (comportement par défaut métier).
    - ``all_objects`` inclut tout (audit, admin).
    - ``deleted_objects`` ne renvoie QUE les supprimés.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True, editable=False)

    objects: ClassVar[Manager[Any]] = ActiveManager()
    all_objects: ClassVar[Manager[Any]] = models.Manager()
    deleted_objects: ClassVar[Manager[Any]] = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
        hard: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """
        Soft delete par défaut. Passer ``hard=True`` pour la suppression physique.

        Réf RM-P04 : un pigeon impliqué dans une reproduction ne peut être hard-deleted.
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return 1, {self._meta.label: 1}

    def restore(self) -> None:
        """Annule un soft delete."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseModel(UUIDPrimaryKeyModel, TimeStampedModel):
    """Modèle de base standard : UUID + timestamps. À utiliser pour la plupart des entités."""

    class Meta:
        abstract = True
