"""Cages + table pivot CageOccupation (RM-CA01..CA05)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.enums import CageStatut
from apps.common.models import BaseModel


class Cage(BaseModel):
    numero = models.CharField(max_length=20, unique=True, db_index=True)
    nom = models.CharField(max_length=100, blank=True, default="")
    superficie = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default="")
    statut_occupation = models.CharField(
        max_length=20,
        choices=CageStatut.choices,
        default=CageStatut.LIBRE,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cages"
    )

    class Meta:
        verbose_name = "Cage"
        verbose_name_plural = "Cages"
        ordering = ("numero",)
        indexes = [
            models.Index(fields=["user", "statut_occupation"], name="idx_cage_user_statut"),
        ]

    def __str__(self) -> str:
        return f"Cage {self.numero}"

    @property
    def is_libre(self) -> bool:
        return self.statut_occupation == CageStatut.LIBRE


class CageOccupation(BaseModel):
    """Trace d'affectation pigeon/couple ↔ cage. ``date_liberation IS NULL`` = active."""

    cage = models.ForeignKey(Cage, on_delete=models.CASCADE, related_name="occupations")
    pigeon = models.ForeignKey(
        "pigeons.Pigeon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occupations",
    )
    couple = models.ForeignKey(
        "couples.Couple",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occupations",
    )
    date_affectation = models.DateTimeField(default=timezone.now)
    date_liberation = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "Occupation de cage"
        verbose_name_plural = "Occupations de cage"
        ordering = ("-date_affectation",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(pigeon__isnull=False, couple__isnull=True)
                    | models.Q(pigeon__isnull=True, couple__isnull=False)
                ),
                name="chk_occupation_pigeon_xor_couple",
            ),
            models.UniqueConstraint(
                fields=["cage"],
                condition=models.Q(date_liberation__isnull=True),
                name="unique_occupation_active_per_cage",
            ),
            models.UniqueConstraint(
                fields=["pigeon"],
                condition=models.Q(date_liberation__isnull=True, pigeon__isnull=False),
                name="unique_occupation_active_per_pigeon",
            ),
            models.UniqueConstraint(
                fields=["couple"],
                condition=models.Q(date_liberation__isnull=True, couple__isnull=False),
                name="unique_occupation_active_per_couple",
            ),
        ]

    @property
    def is_active(self) -> bool:
        return self.date_liberation is None
