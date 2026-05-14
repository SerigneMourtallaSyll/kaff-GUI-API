"""URLs Couples."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.couples.views import CoupleViewSet

app_name = "couples"

router = DefaultRouter()
router.register("", CoupleViewSet, basename="couple")

urlpatterns = router.urls
