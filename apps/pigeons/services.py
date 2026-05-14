"""Services Pigeons — généalogie (RM-R04)."""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q

from apps.pigeons.models import Pigeon


@dataclass(frozen=True)
class Genealogy:
    """Vue généalogique d'un pigeon : parents directs + descendants directs."""

    pigeon: Pigeon
    pere: Pigeon | None
    mere: Pigeon | None
    descendants: list[Pigeon]


def get_genealogy(pigeon: Pigeon) -> Genealogy:
    """Charge parents + descendants directs (1 requête pour les descendants)."""
    descendants = list(
        Pigeon.objects.filter(Q(pere=pigeon) | Q(mere=pigeon))
        .select_related("pere", "mere")
        .order_by("-date_naissance")
    )
    return Genealogy(
        pigeon=pigeon,
        pere=pigeon.pere,
        mere=pigeon.mere,
        descendants=descendants,
    )
