"""
URL configuration principale.

Pattern : /api/v1/<resource>/ — versioning explicite dès le départ.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health(_request: object) -> JsonResponse:
    """Endpoint health check — utilisé par Railway/Render et le mobile au boot."""
    return JsonResponse({"status": "ok", "service": "kaff-gui-api"})


api_v1_patterns = [
    path("auth/", include("apps.users.urls")),
    path("", include("apps.common.urls")),  # Dashboard
    path("pigeons/", include("apps.pigeons.urls")),
    path("cages/", include("apps.cages.urls")),
    path("couples/", include("apps.couples.urls")),
    path("reproductions/", include("apps.reproductions.urls")),
    path("sorties/", include("apps.sorties.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    # API v1
    path("api/v1/", include((api_v1_patterns, "v1"))),
    # OpenAPI schema + Swagger + Redoc
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
