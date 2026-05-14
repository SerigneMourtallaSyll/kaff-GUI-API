from __future__ import annotations

from django.contrib import admin

from apps.cages.models import Cage, CageOccupation


@admin.register(Cage)
class CageAdmin(admin.ModelAdmin):
    list_display = ("numero", "nom", "statut_occupation", "superficie", "user")
    list_filter = ("statut_occupation",)
    search_fields = ("numero", "nom")


@admin.register(CageOccupation)
class CageOccupationAdmin(admin.ModelAdmin):
    list_display = ("cage", "pigeon", "couple", "date_affectation", "date_liberation")
    list_filter = ("date_liberation",)
    autocomplete_fields = ("cage", "pigeon", "couple")
