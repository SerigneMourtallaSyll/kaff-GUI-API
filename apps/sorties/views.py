"""Vues Sorties — lecture seule (US-SOR-04). La création se fait via les actions Pigeon."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.sorties.filters import SortieFilter
from apps.sorties.models import Sortie
from apps.sorties.serializers import SortieSerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet


class SortieViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """RM-S04 — sorties irréversibles, lecture seule via cette ressource."""

    permission_classes = [IsAuthenticated]
    serializer_class = SortieSerializer
    filterset_class = SortieFilter
    ordering_fields = ("date_sortie", "type_sortie", "created_at")
    ordering = ("-date_sortie",)

    def get_queryset(self) -> QuerySet[Sortie]:
        return (
            Sortie.objects.filter(pigeon__user=self.request.user)
            .select_related("pigeon")
            .order_by("-date_sortie", "-created_at")
        )
