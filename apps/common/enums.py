"""
Énumérations métier — miroirs des types ENUM PostgreSQL.

Les valeurs ici DOIVENT rester synchrones avec le schéma DB (voir le document
``Schéma Base De Données Kàff GUI``, § 1.2).
"""

from __future__ import annotations

from django.db import models


class PigeonSexe(models.TextChoices):
    MALE = "MALE", "Mâle"
    FEMALE = "FEMALE", "Femelle"


class PigeonStatut(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    VENDU = "VENDU", "Vendu"
    MORT = "MORT", "Mort"
    PERDU = "PERDU", "Perdu"


class CageStatut(models.TextChoices):
    LIBRE = "LIBRE", "Libre"
    OCCUPE_PIGEON = "OCCUPE_PIGEON", "Occupée par un pigeon"
    OCCUPE_COUPLE = "OCCUPE_COUPLE", "Occupée par un couple"


class CoupleStatut(models.TextChoices):
    ACTIF = "ACTIF", "Actif"
    DISSOUS = "DISSOUS", "Dissous"


class SortieType(models.TextChoices):
    VENTE = "VENTE", "Vente"
    DECES = "DECES", "Décès"
    PERTE = "PERTE", "Perte"
