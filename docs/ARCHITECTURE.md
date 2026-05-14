# Architecture — Kàff GUI API

> Statut : fondation (J1 — scaffolding initial).
> Audience : développeurs + jury Bakeli.

---

## 1. Objectifs

L'API est le backend du projet de validation DTS Bakeli. Au-delà du scope MVP
(cahier des charges § 1.3), elle est ingénieurée aux standards attendus pour
des **applications backend production-grade dans des domaines sensibles**
(banking, fintech). Propriétés concrètes :

- **Modularité** — chaque domaine métier est une app Django isolée (`apps/<x>/`)
  avec ses modèles, ses serializers, ses vues, ses URLs. Aucune app ne dépend
  d'une autre app sœur sans passer par `apps.common`.
- **Maintenabilité** — typage strict (`mypy --strict`), style imposé (`ruff`),
  Conventional Commits, ADRs pour les décisions non triviales.
- **Sécurité** — JWT avec rotation + blacklist, anti-brute-force (axes),
  middleware sécurité Django, conformité OWASP Top 10 (voir cahier des charges § 5).
  Mots de passe hashés Argon2.
- **Performance** — pool de connexions psycopg 3, requêtes optimisées via
  `select_related`/`prefetch_related`, pagination par défaut, throttling DRF.
- **Testabilité** — pytest + pytest-django + factory-boy, settings de test
  dédiés, couverture cible ≥ 70 %.
- **Observabilité** — logs structurés JSON (structlog), request_id par requête,
  endpoint `/health/`, schéma OpenAPI 3 auto-généré.

---

## 2. Layering

```
                  +--------------------------+
                  | URL routing (config/urls)|
                  +-----------+--------------+
                              |
            +-----------------+------------------+
            |                                    |
+-----------v-----------+         +--------------v---------------+
| apps/<x>/views.py     |  uses   | apps/<x>/serializers.py      |
+-----------+-----------+         +--------------+---------------+
            |                                    |
+-----------v-----------+         +--------------v---------------+
| apps/<x>/services.py  |  uses   | apps/<x>/models.py           |
| (logique métier RM-*) |         | (ORM + invariants DB)        |
+-----------+-----------+         +--------------+---------------+
            |                                    |
+-----------v---------------------------v--------+
|  apps/common/  (modèles abstraits, exceptions, |
|  enums, pagination, permissions transverses)   |
+------------------------------------------------+
```

### Règles d'import

- `apps/<x>/` peut importer **uniquement** depuis :
  - `apps.common.*`
  - Django + DRF + libs tierces déclarées dans `pyproject.toml`
- `apps/<x>/` **ne doit pas** importer `apps/<y>/` directement. Les références
  inter-domaines passent par :
  - Une **ForeignKey** au niveau du modèle (Django gère la dépendance),
  - Ou un **service partagé** dans `apps/common/`.
- `config/` peut importer depuis n'importe où (point d'entrée).
- `apps/common/` ne dépend de **rien** sauf Django/DRF.

---

## 3. Anatomie d'une app métier

```
apps/<feature>/
├── apps.py             # AppConfig (label, verbose_name)
├── models.py           # Modèles Django (héritent de apps.common.models.BaseModel)
├── managers.py         # Custom managers (queryset chaining, soft delete...)
├── serializers.py      # DRF serializers (validation + représentation JSON)
├── views.py            # ViewSets / APIViews (permissions, throttling)
├── services.py         # Logique métier complexe (RM-*) — sans dépendance Django ORM si possible
├── filters.py          # django-filter FilterSets
├── permissions.py      # Permissions spécifiques au domaine
├── urls.py             # Routage local (inclus dans config/urls.py)
├── admin.py            # Admin Django
├── migrations/         # Auto-générées par makemigrations
└── tests/
    ├── test_models.py
    ├── test_serializers.py
    ├── test_views.py
    └── test_services.py
```

---

## 4. Modèles de base (apps/common/models.py)

Trois mixins abstraits dont héritent toutes les entités métier :

| Mixin                 | Champs ajoutés                             | Usage                                  |
| --------------------- | ------------------------------------------ | -------------------------------------- |
| `UUIDPrimaryKeyModel` | `id` (UUID v4)                             | Toutes les entités (cf. schéma DB)     |
| `TimeStampedModel`    | `created_at`, `updated_at`                 | Toutes les entités                     |
| `SoftDeleteModel`     | `deleted_at` (+ manager filtrant)          | `pigeons` uniquement (RM-P04)          |
| `BaseModel`           | UUID + timestamps                          | Combo par défaut                       |

Le `SoftDeleteModel.delete()` est surchargé : par défaut soft delete, `hard=True`
pour suppression physique (vérifiée par les services métier selon RM-P04).

---

## 5. Authentification (US-AUTH-01/02/03)

1. **Inscription** — `POST /api/v1/auth/register/` :
   - Validation email unique, mot de passe min 8 chars + 1 chiffre.
   - Hash Argon2.
2. **Login** — `POST /api/v1/auth/login/` :
   - Custom view qui passe par `axes` pour le rate-limit (5 tentatives / 5 min).
   - Retourne `access` (15 min) + `refresh` (7 j).
3. **Refresh** — `POST /api/v1/auth/refresh/` :
   - Rotation activée + blacklist de l'ancien refresh.
4. **Logout** — `POST /api/v1/auth/logout/` :
   - Blackliste le refresh (le mobile a déjà supprimé les tokens localement).
5. **Me** — `GET /api/v1/auth/me/` :
   - Récupère le profil utilisateur courant.

Toutes les routes API (sauf `/auth/register/`, `/auth/login/`, `/health/`,
`/api/docs/`) exigent un Bearer JWT (`IsAuthenticated` par défaut DRF).

---

## 6. Isolation des données (OWASP A01)

- Chaque pigeon / cage / couple / reproduction / sortie possède un FK `user`.
- Les ViewSets filtrent automatiquement `queryset.filter(user=request.user)`.
- La permission `apps.common.permissions.IsOwner` vérifie l'accès objet par objet.

→ Aucun risque qu'un user A accède aux pigeons du user B, même en devinant un UUID.

---

## 7. Gestion d'erreurs

Toutes les erreurs API passent par `apps.common.exceptions.api_exception_handler`
et retournent un format **stable et validable côté mobile (Zod)** :

```json
{
  "error": {
    "code": "validation_error",
    "message": "Les données fournies sont invalides.",
    "details": { "bague": ["Cette bague existe déjà."] },
    "request_id": "abc-123"
  }
}
```

L'exception `BusinessRuleError` est utilisée pour signaler une violation
de règle métier (RM-*) — HTTP 409 Conflict.

---

## 8. Logging & observabilité

- **structlog** configure les logs en format console lisible (dev) et JSON (prod).
- **django-structlog** injecte un `request_id` dans chaque ligne de log.
- Aucun log ne doit contenir de PII (email, password, token).
- L'endpoint `/health/` permet à Railway/Render et au mobile de vérifier le service au boot.

---

## 9. Stratégie de tests

| Niveau         | Outils                                          | Cible                                |
| -------------- | ----------------------------------------------- | ------------------------------------ |
| Unit           | pytest, pure functions                          | services, validators, utils          |
| Models         | pytest-django + factory-boy                     | constraints DB, signals, RM-*        |
| Serializers    | DRF APIRequestFactory                           | validation, représentation           |
| Views          | DRF APIClient                                   | permissions, status codes, payloads  |
| Integration    | pytest --cov, real Postgres test DB             | flux complets (créer pigeon → vente) |

**Coverage cible : ≥ 70 %** (seuil Bakeli, cf. cahier des charges § 7.4).

---

## 10. Déploiement (prévu)

- **Plateforme** — Railway.app (PostgreSQL managé + Django web service).
- **Build** — Nixpacks détecte Python + uv automatiquement.
- **Process** — Gunicorn (`gunicorn config.wsgi --workers 3 --bind 0.0.0.0:$PORT`).
- **Static** — WhiteNoise (compressé + manifest).
- **Variables d'env** — injectées via Railway (jamais dans le repo).

---

## 11. Items ouverts

Tracés dans `docs/adr/` :

- **ADR-001** — Choix de stack initiaux (cette base).
- **À venir** : stratégie de stockage des photos (S3 vs Cloudinary), stratégie
  de cache (Redis ?), stratégie de notifications (v2).
