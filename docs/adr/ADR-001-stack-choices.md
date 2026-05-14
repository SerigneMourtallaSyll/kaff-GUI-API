# ADR-001 — Choix de stack initiaux

- **Date** : 2026-05-14
- **Statut** : Accepté
- **Décideur** : Serigne Mourtalla Syll
- **Contexte** : Démarrage du projet Kàff GUI API (J1).

## Contexte

Le cahier des charges § 4 impose un socle :

- Django 5 + DRF
- PostgreSQL 15
- Auth JWT (simplejwt)
- Déploiement Railway/Render

Au-delà de ce socle, plusieurs choix sont laissés à l'équipe : gestionnaire de
dépendances, structure des apps, linter, type checker, stratégie de logging,
stratégie de tests. Le projet vise des standards production-grade fintech.

## Décisions

### 1. Python 3.12

- Compatible Django 5.1.
- Améliorations de perf et de typage.
- Support assuré jusqu'en 2028.

### 2. uv comme gestionnaire de dépendances

- 10-100× plus rapide que pip / Poetry sur les installs.
- Lockfile déterministe (`uv.lock`).
- Gère aussi les versions de Python.
- Standard 2026 (équivalent Python de pnpm).

**Alternative rejetée** : Poetry — mature, mais lent et l'init/sync coûte 10×
plus que uv.

### 3. Structure `apps/<name>/` + `config/`

- Conforme à la convention cookiecutter-django.
- Mirror du pattern "feature-sliced" du projet mobile.
- Évite le « monolithe à la racine » difficile à scaler.

**Alternative rejetée** : apps à la racine — fonctionnel mais devient confus
au-delà de 4-5 apps.

### 4. psycopg 3 (binary + pool)

- Successeur officiel de psycopg2 (déprécié à terme).
- Pool de connexions natif (pas besoin de pgbouncer en dev).
- Supporte les types Postgres modernes (JSONB, ENUM) nativement.

**Alternative rejetée** : psycopg2-binary — fonctionnel mais plus le standard.

### 5. Ruff comme linter + formatter

- Remplace black + isort + flake8 + pyupgrade en un seul outil 100× plus rapide.
- Configuration unifiée dans `pyproject.toml`.

**Alternative rejetée** : black + isort + flake8 — chaîne classique mais
lente et fragmentée.

### 6. Mypy strict avec stubs Django/DRF

- Équivalent du TypeScript strict côté mobile.
- Permet de détecter les erreurs de typage avant l'exécution.
- `django-stubs` et `djangorestframework-stubs` apportent les types pour les
  champs Django/DRF.

### 7. structlog pour les logs

- Logs structurés JSON-ready pour la prod (parseable par Datadog/Loki/CloudWatch).
- `django-structlog` injecte un `request_id` par requête.
- Mode console lisible en dev.

### 8. django-axes pour la protection brute-force

- Implémente la règle US-AUTH-01 (« blocage 5 min après 5 tentatives échouées »)
  sans avoir à coder un système custom.
- S'intègre nativement avec le système d'auth Django.

### 9. drf-spectacular pour la doc OpenAPI

- Génère un schéma OpenAPI 3 conforme.
- Fournit Swagger UI + Redoc out-of-the-box.
- Compatible avec les générateurs de clients (codegen TS pour le mobile).

### 10. Conventional Commits + commitlint + commitizen

- Cohérent avec le projet mobile.
- Permet de générer automatiquement un changelog.
- Husky exécute commitlint à chaque commit.

## Conséquences

- ✅ Stack moderne et cohérente avec le mobile.
- ✅ Lint + format + typing automatisés via pre-commit.
- ✅ Sécurité par défaut (Argon2, JWT rotation, axes, OWASP middleware).
- ⚠️ Courbe d'apprentissage légèrement plus élevée pour quelqu'un habitué
  au stack Django + pip + flake8.
- ⚠️ uv est encore jeune (sorti 2024) — risque résiduel de bugs.
