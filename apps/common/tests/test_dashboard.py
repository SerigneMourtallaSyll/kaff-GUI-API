"""Tests pour le dashboard."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.cages.models import Cage
from apps.common.enums import CageStatut, CoupleStatut, PigeonStatut
from apps.couples.models import Couple
from apps.pigeons.models import Pigeon
from apps.reproductions.models import Reproduction
from apps.users.models import User


@pytest.fixture
def user(db: None) -> User:
    """Créer un utilisateur de test."""
    return User.objects.create_user(
        email="test@kaff.test",
        password="Test1234!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(user: User) -> APIClient:
    """Client API authentifié."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestDashboard:
    """Tests pour l'endpoint dashboard."""

    def test_dashboard_requires_authentication(self) -> None:
        """Le dashboard nécessite une authentification."""
        client = APIClient()
        url = reverse("v1:common:dashboard")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_empty_voliere(self, authenticated_client: APIClient) -> None:
        """Dashboard avec une volière vide."""
        url = reverse("v1:common:dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["pigeons"]["actifs"] == 0
        assert data["pigeons"]["vendus"] == 0
        assert data["pigeons"]["morts"] == 0
        assert data["pigeons"]["perdus"] == 0
        assert data["cages"]["libres"] == 0
        assert data["cages"]["occupees_pigeon"] == 0
        assert data["cages"]["occupees_couple"] == 0
        assert data["couples_actifs"] == 0
        assert data["dernieres_reproductions"] == []

    def test_dashboard_with_data(self, authenticated_client: APIClient, user: User) -> None:
        """Dashboard avec des données."""
        # Créer des pigeons
        pigeon1 = Pigeon.objects.create(
            user=user,
            bague="TEST001",
            sexe="MALE",
            race="Test",
            date_naissance="2024-01-01",
            statut=PigeonStatut.ACTIF,
        )
        pigeon2 = Pigeon.objects.create(
            user=user,
            bague="TEST002",
            sexe="FEMALE",
            race="Test",
            date_naissance="2024-01-01",
            statut=PigeonStatut.ACTIF,
        )
        Pigeon.objects.create(
            user=user,
            bague="TEST003",
            sexe="MALE",
            race="Test",
            date_naissance="2024-01-01",
            statut=PigeonStatut.VENDU,
        )

        # Créer des cages
        Cage.objects.create(
            user=user,
            numero="C001",
            statut_occupation=CageStatut.LIBRE,
        )
        Cage.objects.create(
            user=user,
            numero="C002",
            statut_occupation=CageStatut.OCCUPE_PIGEON,
        )

        # Créer un couple
        couple = Couple.objects.create(
            user=user,
            male=pigeon1,
            femelle=pigeon2,
            date_formation="2024-02-01",
            statut=CoupleStatut.ACTIF,
        )

        # Créer une reproduction
        Reproduction.objects.create(
            couple=couple,
            date_ponte="2024-03-01",
            nb_pigeonneaux=2,
        )

        url = reverse("v1:common:dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["pigeons"]["actifs"] == 2
        assert data["pigeons"]["vendus"] == 1
        assert data["cages"]["libres"] == 1
        assert data["cages"]["occupees_pigeon"] == 1
        assert data["couples_actifs"] == 1
        assert len(data["dernieres_reproductions"]) == 1
        assert data["dernieres_reproductions"][0]["nb_pigeonneaux"] == 2

    def test_dashboard_isolation_between_users(
        self, authenticated_client: APIClient, user: User, db: None
    ) -> None:
        """Les utilisateurs ne voient que leurs propres données."""
        # Créer un autre utilisateur avec des données
        other_user = User.objects.create_user(
            email="other@kaff.test",
            password="Other1234!",
            first_name="Other",
            last_name="User",
        )
        Pigeon.objects.create(
            user=other_user,
            bague="OTHER001",
            sexe="MALE",
            race="Test",
            date_naissance="2024-01-01",
            statut=PigeonStatut.ACTIF,
        )

        # L'utilisateur authentifié ne doit pas voir les données de l'autre
        url = reverse("v1:common:dashboard")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pigeons"]["actifs"] == 0
