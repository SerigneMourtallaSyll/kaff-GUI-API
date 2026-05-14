# =============================================================================
# Kàff GUI API — commandes de développement
# Usage: make <target>  (ou copier/coller la commande sous PowerShell)
# =============================================================================

.PHONY: help install dev shell migrate makemigrations superuser \
        test test-cov lint lint-fix format typecheck security audit \
        clean docker-pg docker-pg-stop

# Couleurs
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RESET  := \033[0m

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# -------------------------------------------------------------------------
# Installation
# -------------------------------------------------------------------------
install:  ## Installe toutes les dépendances (uv sync)
	uv sync --all-extras
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

# -------------------------------------------------------------------------
# Run
# -------------------------------------------------------------------------
dev:  ## Lance le serveur de développement (http://localhost:8000)
	uv run python manage.py runserver 0.0.0.0:8000

shell:  ## Shell Django interactif (IPython)
	uv run python manage.py shell_plus

# -------------------------------------------------------------------------
# Migrations
# -------------------------------------------------------------------------
migrate:  ## Applique les migrations
	uv run python manage.py migrate

makemigrations:  ## Crée les migrations
	uv run python manage.py makemigrations

superuser:  ## Crée un super-utilisateur admin
	uv run python manage.py createsuperuser

# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------
test:  ## Lance les tests (rapide)
	uv run pytest

test-cov:  ## Lance les tests avec couverture
	uv run pytest --cov --cov-report=term-missing --cov-report=html

# -------------------------------------------------------------------------
# Qualité de code
# -------------------------------------------------------------------------
lint:  ## Lance ruff (linter) + mypy (typing)
	uv run ruff check .
	uv run mypy apps config

lint-fix:  ## Corrige automatiquement les erreurs ruff
	uv run ruff check . --fix

format:  ## Formate le code (ruff format)
	uv run ruff format .

typecheck:  ## Vérifie le typage avec mypy
	uv run mypy apps config

# -------------------------------------------------------------------------
# Sécurité
# -------------------------------------------------------------------------
security:  ## Audit de sécurité du code (bandit)
	uv run bandit -c pyproject.toml -r apps config

audit:  ## Audit des dépendances (pip-audit)
	uv run pip-audit

# -------------------------------------------------------------------------
# Docker — Postgres uniquement (optionnel, pour ceux qui préfèrent)
# -------------------------------------------------------------------------
docker-pg:  ## Lance Postgres 15 dans Docker
	docker run -d --name kaff-pg \
		-e POSTGRES_DB=kaff_gui_dev \
		-e POSTGRES_USER=kaff_dev \
		-e POSTGRES_PASSWORD=kaff_dev_2026 \
		-p 5432:5432 \
		-v kaff-pg-data:/var/lib/postgresql/data \
		postgres:15-alpine

docker-pg-stop:  ## Arrête et supprime le conteneur Postgres
	docker stop kaff-pg && docker rm kaff-pg

# -------------------------------------------------------------------------
# Nettoyage
# -------------------------------------------------------------------------
clean:  ## Supprime caches Python et coverage
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
