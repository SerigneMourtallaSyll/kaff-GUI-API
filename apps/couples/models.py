"""Couples (RM-C01..C04) — mâle + femelle ACTIF, un seul couple actif par pigeon."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.common.enums import CoupleStatut
from apps.common.models import BaseModel


class Couple(BaseModel):
    male = models.ForeignKey(
        "pigeons.Pigeon", on_delete=models.PROTECT, related_name="couples_male"
    )
    femelle = models.ForeignKey(
        "pigeons.Pigeon", on_delete=models.PROTECT, related_name="couples_femelle"
    )
    date_formation = models.DateField()
    date_dissolution = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=10,
        choices=CoupleStatut.choices,
        default=CoupleStatut.ACTIF,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="couples"
    )

    class Meta:
        verbose_name = "Couple"
        verbose_name_plural = "Couples"
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=~Q(male=F("femelle")),
                name="chk_couple_different_pigeons",
            ),
            models.UniqueConstraint(
                fields=["male"],
                condition=Q(statut=CoupleStatut.ACTIF),
                name="unique_male_per_couple_actif",
            ),
            models.UniqueConstraint(
                fields=["femelle"],
                condition=Q(statut=CoupleStatut.ACTIF),
                name="unique_femelle_per_couple_actif",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "statut"], name="idx_couple_user_statut"),
        ]

    def __str__(self) -> str:
        return f"Couple {self.male_id} x {self.femelle_id}"

    @property
    def is_actif(self) -> bool:
        return self.statut == CoupleStatut.ACTIF
