# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### Added
- Configuration complète de l'admin Django pour tous les modules
  - Admin pour reproductions avec fieldsets organisés
  - Admin pour sorties avec sections conditionnelles selon le type
  - Admin personnalisé `KaffAdminSite` avec branding Kàff GUI
- Dashboard API accessible à `/api/v1/dashboard/`
  - Statistiques agrégées des pigeons par statut
  - Statistiques des cages par état d'occupation
  - Nombre de couples actifs
  - Liste des 5 dernières reproductions
  - Serializer `DashboardStatsSerializer` pour génération de schéma OpenAPI
  - Tests complets du dashboard (4 tests : auth, empty, with data, isolation)
- Documentation API complète
  - Configuration Swagger UI avec authentification JWT
  - Schéma OpenAPI 3.0 (JSON et YAML) généré automatiquement
  - Collection Postman v2.1 avec variables d'environnement
  - Script `scripts/generate_api_docs.py` pour génération automatique
  - Swagger UI accessible à `/api/docs/`
  - Redoc accessible à `/api/redoc/`
- Migrations initiales pour toutes les apps (pigeons, cages, couples, reproductions, sorties)
- Services métier pour chaque module avec logique de validation
- Configuration mypy stricte avec overrides pour patterns Django/DRF

### Changed
- Ajout de `search_fields` à `CoupleAdmin` pour support de l'autocomplétion
- Correction du caractère ambigu dans `Couple.__str__()` (× → x)
- Formatage du code avec ruff
- Amélioration de la structure des URLs avec inclusion du dashboard
- Configuration Swagger améliorée avec documentation détaillée des flux d'authentification
- Ajout de type guards `assert user.is_authenticated` dans tous les ViewSets
- Ajout de checks `swagger_fake_view` pour éviter les erreurs de génération de schéma

### Fixed
- Corrections des imports pour respecter les conventions de typage
- Résolution des problèmes de linting ruff
- Résolution de tous les warnings mypy (80 fichiers vérifiés, 0 erreur)
- Correction des annotations de type dans `apps/cages/serializers.py`
- Suppression du commentaire `type: ignore` inutile dans `apps/users/admin.py`

## [0.1.0] - 2026-05-14

### Added
- Structure initiale du projet Django
- Configuration des apps : users, pigeons, cages, couples, reproductions, sorties
- Authentification JWT avec simplejwt
- Configuration CORS et sécurité OWASP
- Tests unitaires avec pytest
- Configuration pre-commit avec ruff, mypy, bandit
- Documentation README complète
