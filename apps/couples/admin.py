from __future__ import annotations

from django.contrib import admin

from apps.couples.models import Couple


@admin.register(Couple)
class CoupleAdmin(admin.ModelAdmin):
    list_display = ("id", "male", "femelle", "statut", "date_formation", "date_dissolution")
    list_filter = ("statut",)
    search_fields = ("male__bague", "femelle__bague")  # Nécessaire pour autocomplete
    autocomplete_fields = ("male", "femelle", "user")
