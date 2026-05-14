"""Reproductions (RM-R01..R04) — portées rattachées à un couple actif."""

from __future__ import annotations

from django.db import models
from django.db.models import F, Q

from apps.common.models import BaseModel


class Reproduction(BaseModel):
    couple = models.ForeignKey(
        "couples.Couple", on_delete=models.CASCADE, related_name="reproductions"
    )
    date_ponte = models.DateField()
    date_eclosion = models.DateField(null=True, blank=True)
    nb_pigeonneaux = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Reproduction"
        verbose_name_plural = "Reproductions"
        ordering = ("-date_ponte", "-created_at")
        constraints = [
            models.CheckConstraint(
                condition=Q(nb_pigeonneaux__gte=0),
                name="chk_repro_nb_positif",
            ),
            models.CheckConstraint(
                condition=Q(date_eclosion__isnull=True) | Q(date_eclosion__gte=F("date_ponte")),
                name="chk_repro_eclosion_date",
            ),
        ]
        indexes = [models.Index(fields=["couple"], name="idx_repro_couple")]

    def __str__(self) -> str:
        return f"Reproduction {self.date_ponte} (couple {self.couple_id})"
