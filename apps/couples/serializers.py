"""Serializers Couples (US-COU-01..03)."""

from __future__ import annotations

from rest_framework import serializers

from apps.common.enums import PigeonSexe, PigeonStatut
from apps.couples.models import Couple
from apps.pigeons.models import Pigeon
from apps.pigeons.serializers import PigeonNestedSerializer


class CoupleListSerializer(serializers.ModelSerializer):
    male = PigeonNestedSerializer(read_only=True)
    femelle = PigeonNestedSerializer(read_only=True)
    nb_reproductions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Couple
        fields = (
            "id",
            "male",
            "femelle",
            "date_formation",
            "date_dissolution",
            "statut",
            "nb_reproductions",
            "created_at",
        )
        read_only_fields = fields


class CoupleCreateSerializer(serializers.ModelSerializer):
    male_id = serializers.PrimaryKeyRelatedField(
        queryset=Pigeon.objects.filter(sexe=PigeonSexe.MALE, statut=PigeonStatut.ACTIF),
        source="male",
    )
    femelle_id = serializers.PrimaryKeyRelatedField(
        queryset=Pigeon.objects.filter(sexe=PigeonSexe.FEMALE, statut=PigeonStatut.ACTIF),
        source="femelle",
    )

    class Meta:
        model = Couple
        fields = ("id", "male_id", "femelle_id", "date_formation")
        read_only_fields = ("id",)


class CoupleRompreSerializer(serializers.Serializer):
    date_dissolution = serializers.DateField()
