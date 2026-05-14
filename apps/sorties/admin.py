"""Admin pour les sorties (vente/décès/perte)."""

from __future__ import annotations

from django.contrib import admin

from apps.sorties.models import Sortie


@admin.register(Sortie)
class SortieAdmin(admin.ModelAdmin):
    """Admin minimaliste pour les sorties."""

    list_display = (
        "pigeon",
        "type_sortie",
        "date_sortie",
        "prix",
        "acheteur",
        "created_at",
    )
    list_filter = ("type_sortie", "date_sortie")
    search_fields = ("pigeon__bague", "acheteur", "cause", "circonstance")
    autocomplete_fields = ("pigeon",)
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "date_sortie"

    fieldsets = (
        (
            "Informations principales",
            {
                "fields": (
                    "pigeon",
                    "type_sortie",
                    "date_sortie",
                )
            },
        ),
        (
            "Détails vente",
            {
                "fields": ("prix", "acheteur"),
                "description": "Obligatoire uniquement pour les ventes",
            },
        ),
        (
            "Détails décès/perte",
            {
                "fields": ("cause", "circonstance"),
                "description": "Optionnel pour décès et perte",
            },
        ),
        (
            "Métadonnées",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
