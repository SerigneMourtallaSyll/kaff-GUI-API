"""Admin pour les reproductions."""

from __future__ import annotations

from django.contrib import admin

from apps.reproductions.models import Reproduction


@admin.register(Reproduction)
class ReproductionAdmin(admin.ModelAdmin):
    """Admin minimaliste pour les reproductions."""

    list_display = (
        "id",
        "couple",
        "date_ponte",
        "date_eclosion",
        "nb_pigeonneaux",
        "created_at",
    )
    list_filter = ("date_ponte", "date_eclosion")
    search_fields = ("couple__male__bague", "couple__femelle__bague", "notes")
    autocomplete_fields = ("couple",)
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "date_ponte"

    fieldsets = (
        (
            "Informations principales",
            {
                "fields": (
                    "couple",
                    "date_ponte",
                    "date_eclosion",
                    "nb_pigeonneaux",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
        (
            "Métadonnées",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
