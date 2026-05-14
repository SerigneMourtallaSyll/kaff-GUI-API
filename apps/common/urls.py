"""URLs transverses (dashboard)."""

from __future__ import annotations

from django.urls import path

from apps.common.views import DashboardView

app_name = "common"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
