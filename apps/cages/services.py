"""
Services Cages — opérations atomiques pour respecter RM-CA01..CA05.

Toute mutation cage ↔ pigeon/couple passe par ces fonctions, qui :
- valident les invariants métier en amont,
- font les inserts / updates en transaction unique,
- maintiennent ``cages.statut_occupation`` synchrone avec ``cage_occupations``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from apps.cages.models import Cage, CageOccupation
from apps.common.enums import CageStatut, CoupleStatut, PigeonStatut
from apps.common.exceptions import BusinessRuleError

if TYPE_CHECKING:
    from apps.couples.models import Couple
    from apps.pigeons.models import Pigeon


@transaction.atomic
def affecter_pigeon(*, cage: Cage, pigeon: Pigeon) -> CageOccupation:
    """RM-CA01/CA03 — affecte un pigeon ACTIF à une cage LIBRE."""
    cage_locked = Cage.objects.select_for_update().get(pk=cage.pk)
    if not cage_locked.is_libre:
        raise BusinessRuleError("La cage n'est pas libre.")
    if pigeon.statut != PigeonStatut.ACTIF or pigeon.deleted_at is not None:
        raise BusinessRuleError("Le pigeon n'est pas ACTIF.")
    if CageOccupation.objects.filter(pigeon=pigeon, date_liberation__isnull=True).exists():
        raise BusinessRuleError("Le pigeon occupe déjà une autre cage.")

    occupation = CageOccupation.objects.create(cage=cage_locked, pigeon=pigeon)
    cage_locked.statut_occupation = CageStatut.OCCUPE_PIGEON
    cage_locked.save(update_fields=["statut_occupation", "updated_at"])
    return occupation


@transaction.atomic
def affecter_couple(*, cage: Cage, couple: Couple) -> CageOccupation:
    """RM-CA01 — affecte un couple ACTIF à une cage LIBRE."""
    cage_locked = Cage.objects.select_for_update().get(pk=cage.pk)
    if not cage_locked.is_libre:
        raise BusinessRuleError("La cage n'est pas libre.")
    if couple.statut != CoupleStatut.ACTIF:
        raise BusinessRuleError("Le couple n'est pas ACTIF.")
    if CageOccupation.objects.filter(couple=couple, date_liberation__isnull=True).exists():
        raise BusinessRuleError("Le couple occupe déjà une autre cage.")

    occupation = CageOccupation.objects.create(cage=cage_locked, couple=couple)
    cage_locked.statut_occupation = CageStatut.OCCUPE_COUPLE
    cage_locked.save(update_fields=["statut_occupation", "updated_at"])
    return occupation


@transaction.atomic
def liberer(*, cage: Cage) -> None:
    """RM-CA04 — ferme l'occupation active de la cage."""
    cage_locked = Cage.objects.select_for_update().get(pk=cage.pk)
    active = (
        CageOccupation.objects.select_for_update()
        .filter(cage=cage_locked, date_liberation__isnull=True)
        .first()
    )
    if active is None:
        cage_locked.statut_occupation = CageStatut.LIBRE
        cage_locked.save(update_fields=["statut_occupation", "updated_at"])
        return

    active.date_liberation = timezone.now()
    active.save(update_fields=["date_liberation"])
    cage_locked.statut_occupation = CageStatut.LIBRE
    cage_locked.save(update_fields=["statut_occupation", "updated_at"])


def liberer_si_occupe_par_pigeon(pigeon: Pigeon) -> None:
    """Helper : libère la cage si le pigeon l'occupe seul (cf. service sorties)."""
    active = CageOccupation.objects.filter(pigeon=pigeon, date_liberation__isnull=True).first()
    if active is not None:
        liberer(cage=active.cage)


def liberer_si_occupe_par_couple(couple: Couple) -> None:
    """Helper : libère la cage si le couple l'occupe (cf. service couples.rompre)."""
    active = CageOccupation.objects.filter(couple=couple, date_liberation__isnull=True).first()
    if active is not None:
        liberer(cage=active.cage)
