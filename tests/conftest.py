"""
Fixtures pytest globales pour les tests d'intégration cross-app.

Voir aussi `apps/<x>/tests/conftest.py` pour les fixtures locales.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def api_client() -> APIClient:
    """Client DRF anonyme."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user_factory) -> Iterator[APIClient]:  # type: ignore[no-untyped-def]
    """Client DRF avec un user authentifié (JWT injecté)."""
    user = user_factory()
    api_client.force_authenticate(user=user)
    yield api_client
    api_client.force_authenticate(user=None)
