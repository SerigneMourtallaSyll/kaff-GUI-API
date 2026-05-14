"""Services Reproductions — enregistrement + création des pigeonneaux (RM-R01..R04)."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from django.db import transaction

from apps.common.enums import CoupleStatut, PigeonStatut
from apps.common.exceptions import BusinessRuleError
from apps.pigeons.models import Pigeon
from apps.reproductions.models import Reproduction

if TYPE_CHECKING:
    from datetime import date as _date

    from apps.couples.models import Couple


class PigeonneauInput(TypedDict, total=False):
    bague: str
    sexe: str
    race: str
    date_naissance: _date | None
    couleur: str
    poids: float | None


@transaction.atomic
def enregistrer_reproduction(
    *,
    couple: Couple,
    date_ponte: _date,
    date_eclosion: _date | None = None,
    nb_pigeonneaux: int = 0,
    notes: str = "",
) -> Reproduction:
    """RM-R01/R02 — couple ACTIF requis ; date_eclosion ≥ date_ponte ; nb ≥ 0."""
    if couple.statut != CoupleStatut.ACTIF:
        raise BusinessRuleError("Le couple n'est pas ACTIF.")
    if nb_pigeonneaux < 0:
        raise BusinessRuleError("Le nombre de pigeonneaux doit être >= 0.")
    if date_eclosion is not None and date_eclosion < date_ponte:
        raise BusinessRuleError("La date d'éclosion doit être >= à la date de ponte.")

    return Reproduction.objects.create(
        couple=couple,
        date_ponte=date_ponte,
        date_eclosion=date_eclosion,
        nb_pigeonneaux=nb_pigeonneaux,
        notes=notes,
    )


@transaction.atomic
def creer_pigeonneaux(
    *, reproduction: Reproduction, pigeonneaux: list[PigeonneauInput]
) -> list[Pigeon]:
    """
    RM-R03 — crée chaque pigeonneau avec père/mère = parents du couple.

    Refuse si plus de pigeonneaux que ``nb_pigeonneaux`` ne sont fournis.
    """
    if len(pigeonneaux) > reproduction.nb_pigeonneaux:
        raise BusinessRuleError(
            f"Trop de pigeonneaux ({len(pigeonneaux)}) pour cette reproduction "
            f"(nb_pigeonneaux={reproduction.nb_pigeonneaux})."
        )

    couple = reproduction.couple
    default_birth = reproduction.date_eclosion or reproduction.date_ponte
    created: list[Pigeon] = []

    for data in pigeonneaux:
        bague = data.get("bague", "").strip()
        if not bague:
            raise BusinessRuleError("Chaque pigeonneau doit avoir une bague.")
        if Pigeon.objects.filter(bague=bague).exists():
            raise BusinessRuleError(f"La bague '{bague}' est déjà utilisée.")

        pigeonneau = Pigeon.objects.create(
            bague=bague,
            sexe=data.get("sexe") or "",
            race=data.get("race", "") or couple.male.race,
            date_naissance=data.get("date_naissance") or default_birth,
            couleur=data.get("couleur") or "",
            poids=data.get("poids"),
            pere=couple.male,
            mere=couple.femelle,
            user=couple.user,
            statut=PigeonStatut.ACTIF,
        )
        created.append(pigeonneau)

    return created
