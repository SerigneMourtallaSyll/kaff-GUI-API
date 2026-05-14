from __future__ import annotations

from django.apps import AppConfig


class ReproductionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reproductions"
    label = "reproductions"
    verbose_name = "Reproductions et généalogie"
