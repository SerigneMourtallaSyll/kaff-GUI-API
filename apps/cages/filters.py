"""Filtres Cages — par statut d'occupation."""

from __future__ import annotations

from django_filters import rest_framework as filters

from apps.cages.models import Cage


class CageFilter(filters.FilterSet):
    class Meta:
        model = Cage
        fields = {
            "statut_occupation": ["exact", "in"],
            "numero": ["exact", "icontains"],
        }
