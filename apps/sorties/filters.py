"""Filtres Sorties — par type et période (US-SOR-04)."""

from __future__ import annotations

from django_filters import rest_framework as filters

from apps.sorties.models import Sortie


class SortieFilter(filters.FilterSet):
    class Meta:
        model = Sortie
        fields = {
            "type_sortie": ["exact", "in"],
            "date_sortie": ["exact", "gte", "lte"],
        }
