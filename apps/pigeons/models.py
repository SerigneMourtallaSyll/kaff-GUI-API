"""Pigeons — entité centrale, soft delete, auto-référence parents (RM-P01..P05)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.common.enums import PigeonSexe, PigeonStatut
from apps.common.models import BaseModel, SoftDeleteModel


class Pigeon(BaseModel, SoftDeleteModel):
    bague = models.CharField(max_length=50, unique=True, db_index=True)
    sexe = models.CharField(max_length=10, choices=PigeonSexe.choices)
    race = models.CharField(max_length=100)
    date_naissance = models.DateField()
    couleur = models.CharField(max_length=100, blank=True, default="")
    poids = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    photo_url = models.TextField(blank=True, default="")
    statut = models.CharField(
        max_length=10, choices=PigeonStatut.choices, default=PigeonStatut.ACTIF, db_index=True
    )
    pere = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enfants_par_pere",
        limit_choices_to={"sexe": PigeonSexe.MALE},
    )
    mere = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enfants_par_mere",
        limit_choices_to={"sexe": PigeonSexe.FEMALE},
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pigeons"
    )

    class Meta:
        verbose_name = "Pigeon"
        verbose_name_plural = "Pigeons"
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=~Q(pere=F("id")) & ~Q(mere=F("id")),
                name="chk_pigeon_not_own_parent",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "statut"], name="idx_pigeon_user_statut"),
            models.Index(fields=["pere"], name="idx_pigeon_pere"),
            models.Index(fields=["mere"], name="idx_pigeon_mere"),
        ]

    def __str__(self) -> str:
        return f"{self.bague} ({self.sexe})"

    @property
    def is_actif(self) -> bool:
        return self.statut == PigeonStatut.ACTIF and self.deleted_at is None

    @property
    def age_jours(self) -> int:
        from datetime import date

        return (date.today() - self.date_naissance).days
