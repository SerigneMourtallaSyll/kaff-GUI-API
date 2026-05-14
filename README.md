# Kàff GUI — API REST

> API REST de gestion de volière colombophile pour Baay Pitàq.
> Backend du projet **Kàff GUI** — projet de validation DTS Bakeli (mai 2026).

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.1-success.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/types-mypy%20strict-blue.svg)](http://mypy-lang.org/)

---

## 🎯 Objectif

Permettre à un colombophile de gérer intégralement sa volière depuis son téléphone :
pigeons, cages, couples, reproductions, généalogie, sorties (vente/décès/perte).

Côté technique, l'API est ingénieurée aux standards d'applications **production-grade
en domaines sensibles** (banking/fintech) : architecture modulaire, typage strict,
soft delete, JWT avec rotation et blacklist, anti-brute-force, OWASP Top 10.

L'application mobile cliente est dans le dépôt voisin `Kaff-GUI-mobile/`.

---

## 🏗️ Stack

| Couche               | Choix                                              |
| -------------------- | -------------------------------------------------- |
| Runtime              | Python 3.12                                        |
| Web                  | Django 5.1 + Django REST Framework 3.15            |
| Base de données      | PostgreSQL 15 (driver psycopg 3 avec pool)         |
| Auth                 | JWT (simplejwt) + token_blacklist + django-axes    |
| Doc API              | drf-spectacular (OpenAPI 3, Swagger, Redoc)        |
| Gestionnaire deps    | uv (Astral)                                        |
| Lint/format          | ruff                                               |
| Type checking        | mypy + django-stubs + djangorestframework-stubs    |
| Tests                | pytest + pytest-django + factory-boy + coverage    |
| Logs                 | structlog (JSON en prod)                           |
| Sécurité             | bandit, gitleaks, pip-audit, axes                  |
| Conventions commits  | Conventional Commits (commitlint + commitizen)     |
| Prod                 | Gunicorn + WhiteNoise + Railway/Render             |

---

## 🚀 Démarrage rapide

### Prérequis

- **Python 3.12** — [python.org](https://www.python.org/downloads/)
- **PostgreSQL 15** — [postgresql.org](https://www.postgresql.org/download/) (ou via Docker)
- **uv** — `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Node.js 20+** (uniquement pour husky/commitlint)

### Installation

```powershell
# 1. Cloner et entrer dans le dossier
git clone https://github.com/SerigneMourtallaSyll/kaff-GUI-API.git
cd kaff-GUI-API

# 2. Configurer l'environnement
copy .env.example .env
# Éditer .env si nécessaire (DATABASE_URL, SECRET_KEY...)

# 3. Installer les dépendances Python (uv crée le venv automatiquement)
uv sync --all-extras

# 4. Installer husky pour commitlint
npm install

# 5. Créer la base de données Postgres
# Via psql ou pgAdmin :
#   CREATE USER kaff_dev WITH PASSWORD 'kaff_dev_2026';
#   CREATE DATABASE kaff_gui_dev OWNER kaff_dev;

# 6. Appliquer les migrations
uv run python manage.py migrate

# 7. Créer un super-utilisateur (pour l'admin)
uv run python manage.py createsuperuser

# 8. Installer les hooks pre-commit
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# 9. Lancer le serveur
uv run python manage.py runserver
```

Le serveur est dispo sur **http://localhost:8000/** :

- `http://localhost:8000/health/` — health check
- `http://localhost:8000/admin/` — admin Django
- `http://localhost:8000/api/docs/` — Swagger UI
- `http://localhost:8000/api/redoc/` — Redoc
- `http://localhost:8000/api/schema/` — OpenAPI 3 schema JSON

---

## 📁 Structure du projet

```
kaff-GUI-API/
├── apps/                          # Code métier — une app Django = un domaine
│   ├── common/                    # Briques transverses (base models, pagination, exceptions, enums)
│   ├── users/                     # Auth + User custom (email-based, UUID)
│   ├── pigeons/                   # Pigeons + soft delete + généalogie
│   ├── cages/                     # Cages + occupations
│   ├── couples/                   # Couples (formation/dissolution)
│   ├── reproductions/             # Reproductions + arbre généalogique
│   └── sorties/                   # Sorties (vente/décès/perte)
│
├── config/                        # Configuration projet
│   ├── settings/
│   │   ├── base.py                # Config commune (sécurité, DRF, JWT, logs)
│   │   ├── development.py         # Dev local (DEBUG, toolbar, CORS large)
│   │   ├── production.py          # Prod (HSTS, SSL, durcissement OWASP)
│   │   └── testing.py             # Tests (hashers rapides, axes off)
│   ├── urls.py                    # Routage principal /api/v1/
│   ├── wsgi.py                    # Entrypoint Gunicorn
│   └── asgi.py                    # Entrypoint Uvicorn (websockets futurs)
│
├── docs/
│   ├── ARCHITECTURE.md            # Description de l'architecture
│   └── adr/                       # Architecture Decision Records
│
├── tests/                         # Tests d'intégration cross-app
├── manage.py
├── pyproject.toml                 # Deps + config ruff/mypy/pytest/coverage
├── .env.example                   # Template de configuration
├── .pre-commit-config.yaml        # Hooks Git (ruff, mypy, gitleaks, bandit)
├── commitlint.config.js           # Conventional Commits
├── package.json                   # husky uniquement
└── Makefile                       # Raccourcis de commandes
```

---

## 🧪 Commandes utiles

| Action               | Commande                                 |
| -------------------- | ---------------------------------------- |
| Serveur dev          | `uv run python manage.py runserver`      |
| Shell Django (IPython)| `uv run python manage.py shell_plus`    |
| Migrations           | `uv run python manage.py makemigrations` |
| Appliquer migrations | `uv run python manage.py migrate`        |
| Tests                | `uv run pytest`                          |
| Tests + couverture   | `uv run pytest --cov`                    |
| Linter               | `uv run ruff check .`                    |
| Auto-fix linter      | `uv run ruff check . --fix`              |
| Formater             | `uv run ruff format .`                   |
| Typage               | `uv run mypy apps config`                |
| Audit sécurité       | `uv run bandit -c pyproject.toml -r apps config` |
| Audit dépendances    | `uv run pip-audit`                       |

Toutes ces commandes sont également dispos comme cibles `make` (voir `Makefile`).

---

## 📐 Conventions

- **Commits** — [Conventional Commits](https://www.conventionalcommits.org/) :
  `feat(scope): ...`, `fix(scope): ...`, etc. Scopes autorisés dans `commitlint.config.js`.
- **Branches** — `feat/<scope>-<resume>`, `fix/<scope>-<bug>`, `docs/<sujet>`.
- **Style** — `ruff` impose le format, `mypy --strict` impose le typage.
- **Tests** — coverage minimum **70 %** (cible Bakeli). RM critiques doivent avoir des tests.
- **Sécurité** — jamais de secret hardcodé, jamais de `DEBUG=True` en prod, toujours
  passer par `apps/common/exceptions.py` pour les erreurs métier.

---

## 🔗 Liens

- Spec métier : voir `Cahier des charges Kàff GUI.docx.md` (dossier parent).
- Schéma DB : voir `Schéma Base De Données Kàff GUI.docx.md` (dossier parent).
- User stories : voir `Users stories Kàff-GUI.docx` (dossier parent).
- Architecture détaillée : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- ADRs : [docs/adr/](docs/adr/).
