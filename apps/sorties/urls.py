"""URLs Sorties — lecture seule."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.sorties.views import SortieViewSet

app_name = "sorties"

router = DefaultRouter()
router.register("", SortieViewSet, basename="sortie")

urlpatterns = router.urls
