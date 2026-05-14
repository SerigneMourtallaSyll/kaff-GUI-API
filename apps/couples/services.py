"""Services Couples — formation et dissolution (RM-C01..C04)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from apps.common.enums import CoupleStatut, PigeonSexe, PigeonStatut
from apps.common.exceptions import BusinessRuleError
from apps.couples.models import Couple

if TYPE_CHECKING:
    from datetime import date as _date

    from apps.pigeons.models import Pigeon
    from apps.users.models import User


@transaction.atomic
def former_couple(*, male: Pigeon, femelle: Pigeon, date_formation: _date, user: User) -> Couple:
    """RM-C01/C02 — vérifie sexes, statut ACTIF, et absence de couple actif existant."""
    if male.sexe != PigeonSexe.MALE:
        raise BusinessRuleError("Le pigeon mâle attendu n'a pas le sexe MALE.")
    if femelle.sexe != PigeonSexe.FEMALE:
        raise BusinessRuleError("Le pigeon femelle attendu n'a pas le sexe FEMALE.")
    if male.pk == femelle.pk:
        raise BusinessRuleError("Mâle et femelle doivent être différents.")
    if male.statut != PigeonStatut.ACTIF or male.deleted_at is not None:
        raise BusinessRuleError("Le mâle n'est pas ACTIF.")
    if femelle.statut != PigeonStatut.ACTIF or femelle.deleted_at is not None:
        raise BusinessRuleError("La femelle n'est pas ACTIVE.")

    if Couple.objects.filter(male=male, statut=CoupleStatut.ACTIF).exists():
        raise BusinessRuleError("Le mâle est déjà dans un couple actif.")
    if Couple.objects.filter(femelle=femelle, statut=CoupleStatut.ACTIF).exists():
        raise BusinessRuleError("La femelle est déjà dans un couple actif.")

    return Couple.objects.create(
        male=male,
        femelle=femelle,
        date_formation=date_formation,
        user=user,
    )


@transaction.atomic
def rompre_couple(*, couple: Couple, date_dissolution: _date) -> Couple:
    """RM-C03/C04 — archive le couple, libère la cage si occupée."""
    from apps.cages.services import liberer_si_occupe_par_couple

    if couple.statut != CoupleStatut.ACTIF:
        raise BusinessRuleError("Le couple n'est pas ACTIF.")
    if date_dissolution < couple.date_formation:
        raise BusinessRuleError(
            "La date de dissolution doit être postérieure à la date de formation."
        )

    couple.statut = CoupleStatut.DISSOUS
    couple.date_dissolution = date_dissolution
    couple.save(update_fields=["statut", "date_dissolution", "updated_at"])

    liberer_si_occupe_par_couple(couple)
    return couple
