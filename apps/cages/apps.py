from __future__ import annotations

from django.apps import AppConfig


class CagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cages"
    label = "cages"
    verbose_name = "Cages et occupations"
