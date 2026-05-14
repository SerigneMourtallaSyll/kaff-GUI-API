"""Serializers Sorties (US-SOR-01..04)."""

from __future__ import annotations

from rest_framework import serializers

from apps.sorties.models import Sortie


class SortieSerializer(serializers.ModelSerializer):
    """Lecture seule — les sorties sont irréversibles (RM-S04)."""

    class Meta:
        model = Sortie
        fields = (
            "id",
            "pigeon",
            "type_sortie",
            "date_sortie",
            "prix",
            "acheteur",
            "cause",
            "circonstance",
            "created_at",
        )
        read_only_fields = fields


class VenteInputSerializer(serializers.Serializer):
    """US-SOR-01 — date, prix, acheteur obligatoires."""

    date_sortie = serializers.DateField()
    prix = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    acheteur = serializers.CharField(max_length=200)


class DecesInputSerializer(serializers.Serializer):
    """US-SOR-02 — date obligatoire, cause optionnelle."""

    date_sortie = serializers.DateField()
    cause = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")


class PerteInputSerializer(serializers.Serializer):
    """US-SOR-03 — date obligatoire, circonstance optionnelle."""

    date_sortie = serializers.DateField()
    circonstance = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )
