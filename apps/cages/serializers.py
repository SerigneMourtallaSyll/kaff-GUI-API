"""Serializers Cages + Occupations (US-CAG-01..06)."""

from __future__ import annotations

from rest_framework import serializers

from apps.cages.models import Cage, CageOccupation


class CageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cage
        fields = (
            "id",
            "numero",
            "nom",
            "superficie",
            "description",
            "statut_occupation",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "statut_occupation", "created_at", "updated_at")


class CageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cage
        fields = ("id", "numero", "nom", "superficie", "description")
        read_only_fields = ("id",)

    def validate_numero(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le numéro de cage est obligatoire.")
        if Cage.objects.filter(numero=value).exists():
            raise serializers.ValidationError("Ce numéro de cage est déjà utilisé.")
        return value


class OccupationPigeonSerializer(serializers.Serializer):
    """Détail occupant pigeon dans la visualisation volière."""

    id = serializers.UUIDField()
    bague = serializers.CharField()
    sexe = serializers.CharField()
    race = serializers.CharField()


class OccupationCoupleSerializer(serializers.Serializer):
    """Détail occupant couple dans la visualisation volière."""

    id = serializers.UUIDField()
    male_bague = serializers.CharField()
    femelle_bague = serializers.CharField()


class VolereCageSerializer(serializers.Serializer):
    """Une case de la grille de visualisation (US-CAG-01)."""

    id = serializers.UUIDField()
    numero = serializers.CharField()
    nom = serializers.CharField()
    statut_occupation = serializers.CharField()
    color = serializers.CharField()
    pigeon = OccupationPigeonSerializer(allow_null=True)
    couple = OccupationCoupleSerializer(allow_null=True)


class CageOccupationSerializer(serializers.ModelSerializer):
    pigeon = serializers.PrimaryKeyRelatedField(read_only=True)
    couple = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CageOccupation
        fields = (
            "id",
            "cage",
            "pigeon",
            "couple",
            "date_affectation",
            "date_liberation",
        )
        read_only_fields = fields


# ----- Actions sur une cage --------------------------------------------------
class AffecterPigeonInputSerializer(serializers.Serializer):
    pigeon_id = serializers.UUIDField()


class AffecterCoupleInputSerializer(serializers.Serializer):
    couple_id = serializers.UUIDField()
