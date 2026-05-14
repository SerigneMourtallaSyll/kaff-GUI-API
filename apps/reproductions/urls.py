"""URLs Reproductions."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.reproductions.views import ReproductionViewSet

app_name = "reproductions"

router = DefaultRouter()
router.register("", ReproductionViewSet, basename="reproduction")

urlpatterns = router.urls
