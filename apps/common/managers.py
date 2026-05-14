"""Managers réutilisables — soft delete et requêtes courantes."""

from __future__ import annotations

from typing import Any

from django.db import models


class SoftDeleteQuerySet(models.QuerySet[Any]):
    """QuerySet conscient du soft delete."""

    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=False)


class ActiveManager(models.Manager[Any]):
    """Manager par défaut : n'expose que les enregistrements non supprimés."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)

    def all_with_deleted(self) -> models.QuerySet[Any]:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteManager(models.Manager[Any]):
    """Ne renvoie QUE les enregistrements soft-deleted (pour audit/admin)."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=False)
