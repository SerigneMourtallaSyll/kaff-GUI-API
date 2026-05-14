"""Configuration personnalisée de l'admin Django pour Kàff GUI."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import AdminSite


class KaffAdminSite(AdminSite):
    """Admin personnalisé pour Kàff GUI."""

    site_header = "Kàff GUI — Administration"
    site_title = "Kàff GUI Admin"
    index_title = "Gestion de la volière"
    site_url = "/api/v1/dashboard/"  # Lien vers le dashboard API
    enable_nav_sidebar = True


# Remplacer le site admin par défaut
admin.site = KaffAdminSite()
admin.sites.site = admin.site
