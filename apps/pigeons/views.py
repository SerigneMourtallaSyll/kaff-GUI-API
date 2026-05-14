"""Vues Pigeons (US-PIG-01..04 + généalogie US-REP-03)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.pigeons.filters import PigeonFilter
from apps.pigeons.models import Pigeon
from apps.pigeons.serializers import (
    GenealogySerializer,
    PigeonCreateSerializer,
    PigeonDetailSerializer,
    PigeonListSerializer,
    PigeonUpdateSerializer,
)
from apps.pigeons.services import get_genealogy
from apps.sorties.serializers import (
    DecesInputSerializer,
    PerteInputSerializer,
    VenteInputSerializer,
)
from apps.sorties.services import declarer_deces, declarer_perte, vendre

if TYPE_CHECKING:
    from django.db.models import QuerySet


class PigeonViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD pigeons + actions de sortie + généalogie."""

    permission_classes = [IsAuthenticated]
    filterset_class = PigeonFilter
    search_fields = ("bague", "race")
    ordering_fields = ("created_at", "date_naissance", "bague", "statut")
    ordering = ("-created_at",)

    def get_queryset(self) -> QuerySet[Pigeon]:
        return (
            Pigeon.objects.filter(user=self.request.user)
            .select_related("pere", "mere")
            .order_by("-created_at")
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        action_name = getattr(self, "action", None)
        if action_name == "create":
            return PigeonCreateSerializer
        if action_name in {"update", "partial_update"}:
            return PigeonUpdateSerializer
        if action_name == "list":
            return PigeonListSerializer
        return PigeonDetailSerializer

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["pigeons"],
        responses=GenealogySerializer,
        description="Arbre généalogique : père, mère, descendants directs (US-REP-03).",
    )
    @action(detail=True, methods=["get"], url_path="genealogy")
    def genealogy(self, request, pk=None):  # type: ignore[no-untyped-def]
        pigeon = self.get_object()
        data = get_genealogy(pigeon)
        return Response(
            {
                "pigeon": {
                    "id": data.pigeon.id,
                    "bague": data.pigeon.bague,
                    "sexe": data.pigeon.sexe,
                    "race": data.pigeon.race,
                    "statut": data.pigeon.statut,
                },
                "pere": None
                if data.pere is None
                else {
                    "id": data.pere.id,
                    "bague": data.pere.bague,
                    "sexe": data.pere.sexe,
                    "race": data.pere.race,
                    "statut": data.pere.statut,
                },
                "mere": None
                if data.mere is None
                else {
                    "id": data.mere.id,
                    "bague": data.mere.bague,
                    "sexe": data.mere.sexe,
                    "race": data.mere.race,
                    "statut": data.mere.statut,
                },
                "descendants": [
                    {
                        "id": d.id,
                        "bague": d.bague,
                        "sexe": d.sexe,
                        "race": d.race,
                        "statut": d.statut,
                    }
                    for d in data.descendants
                ],
            }
        )

    # ---- Actions de sortie (US-SOR-01/02/03) -------------------------------
    @extend_schema(tags=["pigeons"], request=VenteInputSerializer)
    @action(detail=True, methods=["post"], url_path="vendre")
    def vendre(self, request, pk=None):  # type: ignore[no-untyped-def]
        pigeon = self.get_object()
        ser = VenteInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sortie = vendre(pigeon=pigeon, **ser.validated_data)
        return Response(
            {"id": sortie.id, "type_sortie": sortie.type_sortie}, status=status.HTTP_201_CREATED
        )

    @extend_schema(tags=["pigeons"], request=DecesInputSerializer)
    @action(detail=True, methods=["post"], url_path="declarer-deces")
    def declarer_deces(self, request, pk=None):  # type: ignore[no-untyped-def]
        pigeon = self.get_object()
        ser = DecesInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sortie = declarer_deces(pigeon=pigeon, **ser.validated_data)
        return Response(
            {"id": sortie.id, "type_sortie": sortie.type_sortie}, status=status.HTTP_201_CREATED
        )

    @extend_schema(tags=["pigeons"], request=PerteInputSerializer)
    @action(detail=True, methods=["post"], url_path="declarer-perte")
    def declarer_perte(self, request, pk=None):  # type: ignore[no-untyped-def]
        pigeon = self.get_object()
        ser = PerteInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sortie = declarer_perte(pigeon=pigeon, **ser.validated_data)
        return Response(
            {"id": sortie.id, "type_sortie": sortie.type_sortie}, status=status.HTTP_201_CREATED
        )
