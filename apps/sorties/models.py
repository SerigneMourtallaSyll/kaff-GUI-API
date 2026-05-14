"""Sorties (RM-S01..S04) — événements irréversibles de fin de vie."""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.common.enums import SortieType
from apps.common.models import BaseModel


class Sortie(BaseModel):
    pigeon = models.OneToOneField("pigeons.Pigeon", on_delete=models.PROTECT, related_name="sortie")
    type_sortie = models.CharField(max_length=10, choices=SortieType.choices)
    date_sortie = models.DateField()
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    acheteur = models.CharField(max_length=200, blank=True, default="")
    cause = models.TextField(blank=True, default="")
    circonstance = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Sortie"
        verbose_name_plural = "Sorties"
        ordering = ("-date_sortie", "-created_at")
        constraints = [
            models.CheckConstraint(
                condition=(
                    ~Q(type_sortie=SortieType.VENTE) | (Q(prix__isnull=False) & ~Q(acheteur=""))
                ),
                name="chk_sortie_vente_complete",
            ),
        ]
        indexes = [
            models.Index(fields=["type_sortie", "-date_sortie"], name="idx_sortie_type_date"),
        ]

    def __str__(self) -> str:
        return f"{self.type_sortie} — {self.pigeon_id} ({self.date_sortie})"
