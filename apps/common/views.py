"""Dashboard agrégé — KPIs cross-app (§ 3.2 du cahier des charges)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cages.models import Cage
from apps.common.enums import CageStatut, CoupleStatut, PigeonStatut
from apps.couples.models import Couple
from apps.pigeons.models import Pigeon
from apps.reproductions.models import Reproduction

if TYPE_CHECKING:
    from rest_framework.request import Request


class DashboardView(APIView):
    """Statistiques agrégées en quelques requêtes — pas de N+1."""

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["dashboard"])
    def get(self, request: Request) -> Response:
        user = request.user

        pigeons_stats = Pigeon.objects.filter(user=user, deleted_at__isnull=True).aggregate(
            actifs=Count("id", filter=Q(statut=PigeonStatut.ACTIF)),
            vendus=Count("id", filter=Q(statut=PigeonStatut.VENDU)),
            morts=Count("id", filter=Q(statut=PigeonStatut.MORT)),
            perdus=Count("id", filter=Q(statut=PigeonStatut.PERDU)),
        )

        cages_stats = Cage.objects.filter(user=user).aggregate(
            libres=Count("id", filter=Q(statut_occupation=CageStatut.LIBRE)),
            occupees_pigeon=Count("id", filter=Q(statut_occupation=CageStatut.OCCUPE_PIGEON)),
            occupees_couple=Count("id", filter=Q(statut_occupation=CageStatut.OCCUPE_COUPLE)),
        )

        couples_actifs = Couple.objects.filter(user=user, statut=CoupleStatut.ACTIF).count()

        dernieres_reproductions = (
            Reproduction.objects.filter(couple__user=user)
            .select_related("couple__male", "couple__femelle")
            .order_by("-created_at")[:5]
        )
        dernieres = [
            {
                "id": str(r.id),
                "couple_id": str(r.couple_id),
                "date_ponte": r.date_ponte,
                "date_eclosion": r.date_eclosion,
                "nb_pigeonneaux": r.nb_pigeonneaux,
                "male_bague": r.couple.male.bague,
                "femelle_bague": r.couple.femelle.bague,
            }
            for r in dernieres_reproductions
        ]

        return Response(
            {
                "pigeons": {
                    "actifs": pigeons_stats["actifs"] or 0,
                    "vendus": pigeons_stats["vendus"] or 0,
                    "morts": pigeons_stats["morts"] or 0,
                    "perdus": pigeons_stats["perdus"] or 0,
                },
                "cages": {
                    "libres": cages_stats["libres"] or 0,
                    "occupees_pigeon": cages_stats["occupees_pigeon"] or 0,
                    "occupees_couple": cages_stats["occupees_couple"] or 0,
                },
                "couples_actifs": couples_actifs,
                "dernieres_reproductions": dernieres,
            }
        )
