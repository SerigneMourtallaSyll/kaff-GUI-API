"""URLs Cages."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.cages.views import CageViewSet

app_name = "cages"

router = DefaultRouter()
router.register("", CageViewSet, basename="cage")

urlpatterns = router.urls
