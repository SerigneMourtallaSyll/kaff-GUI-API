"""Serializers Pigeons (US-PIG-01..04)."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.pigeons.models import Pigeon


class PigeonNestedSerializer(serializers.ModelSerializer):
    """Représentation minimaliste utilisée en imbriqué (parents, occupant cage…)."""

    class Meta:
        model = Pigeon
        fields = ("id", "bague", "sexe", "race", "statut")
        read_only_fields = fields


class PigeonListSerializer(serializers.ModelSerializer):
    """Représentation pour la liste — pas d'imbrications coûteuses."""

    age_jours = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pigeon
        fields = (
            "id",
            "bague",
            "sexe",
            "race",
            "date_naissance",
            "age_jours",
            "statut",
            "couleur",
            "photo_url",
        )
        read_only_fields = fields


class PigeonDetailSerializer(serializers.ModelSerializer):
    """Fiche complète (US-PIG-02) — parents directs imbriqués, descendants ailleurs."""

    age_jours = serializers.IntegerField(read_only=True)
    pere = PigeonNestedSerializer(read_only=True)
    mere = PigeonNestedSerializer(read_only=True)

    class Meta:
        model = Pigeon
        fields = (
            "id",
            "bague",
            "sexe",
            "race",
            "date_naissance",
            "age_jours",
            "couleur",
            "poids",
            "photo_url",
            "statut",
            "pere",
            "mere",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "statut",
            "pere",
            "mere",
            "created_at",
            "updated_at",
            "age_jours",
        )


class PigeonCreateSerializer(serializers.ModelSerializer):
    """Création (US-PIG-01) — bague unique, champs obligatoires."""

    class Meta:
        model = Pigeon
        fields = (
            "id",
            "bague",
            "sexe",
            "race",
            "date_naissance",
            "couleur",
            "poids",
            "photo_url",
        )
        read_only_fields = ("id",)

    def validate_bague(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("La bague est obligatoire.")
        if Pigeon.objects.filter(bague=value).exists():
            raise serializers.ValidationError("Cette bague est déjà utilisée.")
        return value


class PigeonUpdateSerializer(serializers.ModelSerializer):
    """Modification (US-PIG-03) — bague immuable (RM-P01), pigeon ACTIF uniquement."""

    class Meta:
        model = Pigeon
        fields = ("race", "couleur", "poids", "photo_url")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance: Pigeon = self.instance  # type: ignore[assignment]
        if instance is not None and not instance.is_actif:
            raise serializers.ValidationError(
                "Seuls les pigeons ACTIF sont modifiables (lecture seule pour VENDU/MORT/PERDU)."
            )
        return attrs


class GenealogySerializer(serializers.Serializer):
    """Réponse de l'endpoint /pigeons/<id>/genealogy/ (US-REP-03)."""

    pigeon = PigeonNestedSerializer()
    pere = PigeonNestedSerializer(allow_null=True)
    mere = PigeonNestedSerializer(allow_null=True)
    descendants = PigeonNestedSerializer(many=True)
