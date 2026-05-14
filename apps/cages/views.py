"""Vues Cages + visualisation volière (US-CAG-01..06 — feature centrale)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cages.filters import CageFilter
from apps.cages.models import Cage, CageOccupation
from apps.cages.serializers import (
    AffecterCoupleInputSerializer,
    AffecterPigeonInputSerializer,
    CageCreateSerializer,
    CageOccupationSerializer,
    CageSerializer,
    VolereCageSerializer,
)
from apps.cages.services import affecter_couple, affecter_pigeon, liberer
from apps.common.enums import CageStatut
from apps.common.exceptions import BusinessRuleError
from apps.couples.models import Couple
from apps.pigeons.models import Pigeon

if TYPE_CHECKING:
    from django.db.models import QuerySet


CAGE_COLORS = {
    CageStatut.LIBRE: "#4CAF50",
    CageStatut.OCCUPE_PIGEON: "#F44336",
    CageStatut.OCCUPE_COUPLE: "#FF9800",
}


class CageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_class = CageFilter
    search_fields = ("numero", "nom")
    ordering_fields = ("numero", "created_at")
    ordering = ("numero",)

    def get_queryset(self) -> QuerySet[Cage]:
        return Cage.objects.filter(user=self.request.user).order_by("numero")

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if getattr(self, "action", None) == "create":
            return CageCreateSerializer
        return CageSerializer

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance: Cage) -> None:
        if not instance.is_libre:
            raise BusinessRuleError(
                "Impossible de supprimer une cage occupée. Libérer la cage d'abord."
            )
        instance.delete()

    # ---- Visualisation volière (US-CAG-01) — feature centrale --------------
    @extend_schema(
        tags=["cages"],
        responses=VolereCageSerializer(many=True),
        description=(
            "Renvoie l'état de toutes les cages avec leur occupant courant. "
            "Code couleur : vert=libre, rouge=pigeon, orange=couple. "
            "Optimisé en 1 requête + 1 prefetch (zéro N+1)."
        ),
    )
    @action(detail=False, methods=["get"], url_path="volet")
    def volet(self, request):  # type: ignore[no-untyped-def]
        cages = (
            Cage.objects.filter(user=request.user)
            .prefetch_related(
                Prefetch(
                    "occupations",
                    queryset=CageOccupation.objects.filter(
                        date_liberation__isnull=True
                    ).select_related("pigeon", "couple__male", "couple__femelle"),
                    to_attr="_occ_actives",
                )
            )
            .order_by("numero")
        )

        payload = []
        for cage in cages:
            active = next(iter(getattr(cage, "_occ_actives", [])), None)
            payload.append(
                {
                    "id": cage.id,
                    "numero": cage.numero,
                    "nom": cage.nom,
                    "statut_occupation": cage.statut_occupation,
                    "color": CAGE_COLORS[CageStatut(cage.statut_occupation)],
                    "pigeon": (
                        {
                            "id": active.pigeon.id,
                            "bague": active.pigeon.bague,
                            "sexe": active.pigeon.sexe,
                            "race": active.pigeon.race,
                        }
                        if active is not None and active.pigeon is not None
                        else None
                    ),
                    "couple": (
                        {
                            "id": active.couple.id,
                            "male_bague": active.couple.male.bague,
                            "femelle_bague": active.couple.femelle.bague,
                        }
                        if active is not None and active.couple is not None
                        else None
                    ),
                }
            )
        return Response(payload)

    # ---- Actions d'occupation (US-CAG-02/03/05) ----------------------------
    @extend_schema(tags=["cages"], request=AffecterPigeonInputSerializer)
    @action(detail=True, methods=["post"], url_path="affecter-pigeon")
    def affecter_pigeon_action(self, request, pk=None):  # type: ignore[no-untyped-def]
        cage = self.get_object()
        ser = AffecterPigeonInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            pigeon = Pigeon.objects.get(pk=ser.validated_data["pigeon_id"], user=request.user)
        except Pigeon.DoesNotExist as exc:
            raise NotFound("Pigeon introuvable.") from exc
        occ = affecter_pigeon(cage=cage, pigeon=pigeon)
        return Response(CageOccupationSerializer(occ).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["cages"], request=AffecterCoupleInputSerializer)
    @action(detail=True, methods=["post"], url_path="affecter-couple")
    def affecter_couple_action(self, request, pk=None):  # type: ignore[no-untyped-def]
        cage = self.get_object()
        ser = AffecterCoupleInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            couple = Couple.objects.get(pk=ser.validated_data["couple_id"], user=request.user)
        except Couple.DoesNotExist as exc:
            raise NotFound("Couple introuvable.") from exc
        occ = affecter_couple(cage=cage, couple=couple)
        return Response(CageOccupationSerializer(occ).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["cages"])
    @action(detail=True, methods=["post"], url_path="liberer")
    def liberer_action(self, request, pk=None):  # type: ignore[no-untyped-def]
        cage = self.get_object()
        liberer(cage=cage)
        return Response(status=status.HTTP_204_NO_CONTENT)
