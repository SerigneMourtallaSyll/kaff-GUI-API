from __future__ import annotations

from django.contrib import admin

from apps.pigeons.models import Pigeon


@admin.register(Pigeon)
class PigeonAdmin(admin.ModelAdmin):
    list_display = ("bague", "sexe", "race", "statut", "date_naissance", "user")
    list_filter = ("statut", "sexe", "race")
    search_fields = ("bague", "race")
    autocomplete_fields = ("pere", "mere", "user")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
