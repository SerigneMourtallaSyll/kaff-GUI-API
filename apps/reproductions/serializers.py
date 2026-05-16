"""Serializers Reproductions + Pigeonneaux (US-REP-01..03)."""

from __future__ import annotations

from rest_framework import serializers

from apps.pigeons.serializers import PigeonNestedSerializer
from apps.reproductions.models import Reproduction


class ReproductionSerializer(serializers.ModelSerializer):
    # Add male and female bague for display
    male_bague = serializers.CharField(source="couple.male.bague", read_only=True)
    femelle_bague = serializers.CharField(source="couple.femelle.bague", read_only=True)

    class Meta:
        model = Reproduction
        fields = (
            "id",
            "couple",
            "date_ponte",
            "date_eclosion",
            "nb_pigeonneaux",
            "notes",
            "created_at",
            "male_bague",
            "femelle_bague",
        )
        read_only_fields = ("id", "created_at", "male_bague", "femelle_bague")


class ReproductionCreateSerializer(serializers.ModelSerializer):
    """US-REP-01."""

    class Meta:
        model = Reproduction
        fields = ("id", "date_ponte", "date_eclosion", "nb_pigeonneaux", "notes")
        read_only_fields = ("id",)


class PigeonneauInputSerializer(serializers.Serializer):
    bague = serializers.CharField(max_length=50)
    sexe = serializers.CharField(max_length=10)
    race = serializers.CharField(max_length=100, required=False, allow_blank=True)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    couleur = serializers.CharField(max_length=100, required=False, allow_blank=True)
    poids = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )


class CreerPigeonneauxInputSerializer(serializers.Serializer):
    """Payload pour POST /reproductions/<id>/pigeonneaux/ (US-REP-02)."""

    pigeonneaux = PigeonneauInputSerializer(many=True)


class CreerPigeonneauxResponseSerializer(serializers.Serializer):
    pigeonneaux = PigeonNestedSerializer(many=True)
