"""Filtres Pigeons (US-PIG-04) — statut / sexe / race / disponibles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Exists, OuterRef, Q
from django_filters import rest_framework as filters

from apps.common.enums import CoupleStatut, PigeonStatut
from apps.pigeons.models import Pigeon

if TYPE_CHECKING:
    from django.db.models import QuerySet


class PigeonFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search", label="Recherche bague/race")
    disponible = filters.BooleanFilter(
        method="filter_disponible", label="Disponibles (ACTIF, sans couple, sans cage)"
    )

    class Meta:
        model = Pigeon
        fields = {
            "statut": ["exact", "in"],
            "sexe": ["exact"],
            "race": ["exact", "icontains"],
        }

    def filter_search(self, queryset: QuerySet[Pigeon], _name: str, value: str) -> QuerySet[Pigeon]:
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(Q(bague__icontains=value) | Q(race__icontains=value))

    def filter_disponible(
        self, queryset: QuerySet[Pigeon], _name: str, value: bool
    ) -> QuerySet[Pigeon]:
        if not value:
            return queryset
        from apps.cages.models import CageOccupation
        from apps.couples.models import Couple

        couples_actifs = Couple.objects.filter(
            Q(male=OuterRef("pk")) | Q(femelle=OuterRef("pk")), statut=CoupleStatut.ACTIF
        )
        cages_occupees = CageOccupation.objects.filter(
            pigeon=OuterRef("pk"), date_liberation__isnull=True
        )
        return (
            queryset.filter(statut=PigeonStatut.ACTIF)
            .annotate(_in_couple=Exists(couples_actifs), _in_cage=Exists(cages_occupees))
            .filter(_in_couple=False, _in_cage=False)
        )
