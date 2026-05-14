"""
Services Sorties — déclaration vente/décès/perte (RM-S01..S04).

Une sortie a 3 effets atomiques :
1. Crée le Sortie (lien 1-1 avec le pigeon, irréversible).
2. Passe le pigeon à VENDU/MORT/PERDU.
3. Libère sa cage (si occupée seul) et dissout son couple actif (RM-P05).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from apps.common.enums import CoupleStatut, PigeonStatut, SortieType
from apps.common.exceptions import BusinessRuleError
from apps.sorties.models import Sortie

if TYPE_CHECKING:
    from datetime import date as _date

    from apps.pigeons.models import Pigeon


def _ensure_pigeon_actif(pigeon: Pigeon) -> None:
    if pigeon.statut != PigeonStatut.ACTIF or pigeon.deleted_at is not None:
        raise BusinessRuleError("Seul un pigeon ACTIF peut faire l'objet d'une sortie.")


@transaction.atomic
def _post_sortie_cleanup(pigeon: Pigeon, nouveau_statut: str) -> None:
    """Effets de bord après création d'une Sortie : statut + cage + couples actifs."""
    from django.db.models import Q
    from django.utils import timezone

    from apps.cages.services import liberer_si_occupe_par_pigeon
    from apps.couples.models import Couple
    from apps.couples.services import rompre_couple

    pigeon.statut = nouveau_statut
    pigeon.save(update_fields=["statut", "updated_at"])

    liberer_si_occupe_par_pigeon(pigeon)

    # Dissoudre tout couple actif du pigeon
    today = timezone.now().date()
    for couple in Couple.objects.filter(
        Q(male=pigeon) | Q(femelle=pigeon), statut=CoupleStatut.ACTIF
    ):
        rompre_couple(couple=couple, date_dissolution=today)


@transaction.atomic
def vendre(*, pigeon: Pigeon, date_sortie: _date, prix: float, acheteur: str) -> Sortie:
    """RM-S01 — date, prix et acheteur obligatoires."""
    _ensure_pigeon_actif(pigeon)
    if not acheteur.strip():
        raise BusinessRuleError("Le nom de l'acheteur est obligatoire.")
    if prix is None or prix < 0:
        raise BusinessRuleError("Le prix doit être >= 0.")

    sortie = Sortie.objects.create(
        pigeon=pigeon,
        type_sortie=SortieType.VENTE,
        date_sortie=date_sortie,
        prix=prix,
        acheteur=acheteur.strip(),
    )
    _post_sortie_cleanup(pigeon, PigeonStatut.VENDU)
    return sortie


@transaction.atomic
def declarer_deces(*, pigeon: Pigeon, date_sortie: _date, cause: str = "") -> Sortie:
    """RM-S02 — date obligatoire, cause optionnelle."""
    _ensure_pigeon_actif(pigeon)
    sortie = Sortie.objects.create(
        pigeon=pigeon,
        type_sortie=SortieType.DECES,
        date_sortie=date_sortie,
        cause=cause,
    )
    _post_sortie_cleanup(pigeon, PigeonStatut.MORT)
    return sortie


@transaction.atomic
def declarer_perte(*, pigeon: Pigeon, date_sortie: _date, circonstance: str = "") -> Sortie:
    """RM-S03 — date obligatoire, circonstance optionnelle."""
    _ensure_pigeon_actif(pigeon)
    sortie = Sortie.objects.create(
        pigeon=pigeon,
        type_sortie=SortieType.PERTE,
        date_sortie=date_sortie,
        circonstance=circonstance,
    )
    _post_sortie_cleanup(pigeon, PigeonStatut.PERDU)
    return sortie
