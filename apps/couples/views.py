"""Vues Couples (US-COU-01..03)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.couples.filters import CoupleFilter
from apps.couples.models import Couple
from apps.couples.serializers import (
    CoupleCreateSerializer,
    CoupleListSerializer,
    CoupleRompreSerializer,
)
from apps.couples.services import former_couple, rompre_couple

if TYPE_CHECKING:
    from django.db.models import QuerySet


class CoupleViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    filterset_class = CoupleFilter
    ordering_fields = ("date_formation", "created_at", "statut")
    ordering = ("-created_at",)

    def get_queryset(self) -> QuerySet[Couple]:
        # Pour la génération du schéma OpenAPI
        if getattr(self, "swagger_fake_view", False):
            return Couple.objects.none()
        user = self.request.user
        assert user.is_authenticated  # Type guard pour mypy (IsAuthenticated garantit cela)
        return (
            Couple.objects.filter(user=user)
            .select_related("male", "femelle")
            .annotate(nb_reproductions=Count("reproductions"))
            .order_by("-created_at")
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if getattr(self, "action", None) == "create":
            return CoupleCreateSerializer
        return CoupleListSerializer

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        ser = CoupleCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        couple = former_couple(
            male=ser.validated_data["male"],
            femelle=ser.validated_data["femelle"],
            date_formation=ser.validated_data["date_formation"],
            user=request.user,
        )
        # Re-fetch via queryset pour bénéficier des annotations
        couple = self.get_queryset().get(pk=couple.pk)
        return Response(CoupleListSerializer(couple).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["couples"], request=CoupleRompreSerializer)
    @action(detail=True, methods=["post"], url_path="rompre")
    def rompre(self, request, pk=None):  # type: ignore[no-untyped-def]
        couple = self.get_object()
        ser = CoupleRompreSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rompre_couple(couple=couple, date_dissolution=ser.validated_data["date_dissolution"])
        couple = self.get_queryset().get(pk=couple.pk)
        return Response(CoupleListSerializer(couple).data)
