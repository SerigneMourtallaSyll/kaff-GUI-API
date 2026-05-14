"""URLs Pigeons — routeur DRF."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.pigeons.views import PigeonViewSet

app_name = "pigeons"

router = DefaultRouter()
router.register("", PigeonViewSet, basename="pigeon")

urlpatterns = router.urls
