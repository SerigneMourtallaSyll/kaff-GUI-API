"""Vues Reproductions (US-REP-01..03)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.couples.models import Couple
from apps.pigeons.serializers import PigeonNestedSerializer
from apps.reproductions.models import Reproduction
from apps.reproductions.serializers import (
    CreerPigeonneauxInputSerializer,
    ReproductionCreateSerializer,
    ReproductionSerializer,
)
from apps.reproductions.services import creer_pigeonneaux, enregistrer_reproduction

if TYPE_CHECKING:
    from django.db.models import QuerySet


class ReproductionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    filterset_fields = ("couple",)
    ordering_fields = ("date_ponte", "date_eclosion", "created_at")
    ordering = ("-date_ponte", "-created_at")

    def get_queryset(self) -> QuerySet[Reproduction]:
        # Pour la génération du schéma OpenAPI
        if getattr(self, "swagger_fake_view", False):
            return Reproduction.objects.none()
        user = self.request.user
        assert user.is_authenticated  # Type guard pour mypy (IsAuthenticated garantit cela)
        return (
            Reproduction.objects.filter(couple__user=user)
            .select_related("couple__male", "couple__femelle")
            .order_by("-date_ponte", "-created_at")
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if getattr(self, "action", None) == "create":
            return ReproductionCreateSerializer
        return ReproductionSerializer

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        couple_id = request.data.get("couple")
        if not couple_id:
            raise ValidationError({"couple": "L'identifiant du couple est obligatoire."})
        try:
            couple = Couple.objects.get(pk=couple_id, user=request.user)
        except Couple.DoesNotExist as exc:
            raise NotFound("Couple introuvable.") from exc

        ser = ReproductionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        repro = enregistrer_reproduction(
            couple=couple,
            date_ponte=ser.validated_data["date_ponte"],
            date_eclosion=ser.validated_data.get("date_eclosion"),
            nb_pigeonneaux=ser.validated_data.get("nb_pigeonneaux", 0),
            notes=ser.validated_data.get("notes", ""),
        )
        return Response(ReproductionSerializer(repro).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["reproductions"], request=CreerPigeonneauxInputSerializer)
    @action(detail=True, methods=["post"], url_path="pigeonneaux")
    def pigeonneaux(self, request, pk=None):  # type: ignore[no-untyped-def]
        reproduction = self.get_object()
        ser = CreerPigeonneauxInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        created = creer_pigeonneaux(
            reproduction=reproduction, pigeonneaux=ser.validated_data["pigeonneaux"]
        )
        return Response(
            {"pigeonneaux": PigeonNestedSerializer(created, many=True).data},
            status=status.HTTP_201_CREATED,
        )
