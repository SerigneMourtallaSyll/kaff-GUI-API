"""Filtres Couples — par statut ACTIF/DISSOUS."""

from __future__ import annotations

from django_filters import rest_framework as filters

from apps.couples.models import Couple


class CoupleFilter(filters.FilterSet):
    class Meta:
        model = Couple
        fields = {"statut": ["exact", "in"]}
