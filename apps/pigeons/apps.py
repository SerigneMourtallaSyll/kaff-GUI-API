from __future__ import annotations

from django.apps import AppConfig


class PigeonsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pigeons"
    label = "pigeons"
    verbose_name = "Pigeons"
