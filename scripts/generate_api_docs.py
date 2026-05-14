#!/usr/bin/env python
"""
Script pour générer la documentation API :
- Schéma OpenAPI 3.0 (JSON/YAML)
- Collection Postman

Usage:
    python scripts/generate_api_docs.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from django.core.management import call_command  # noqa: E402


def generate_openapi_schema() -> None:
    """Génère le schéma OpenAPI 3.0 en JSON et YAML."""
    docs_dir = Path(__file__).parent.parent / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Générer le schéma JSON
    json_path = docs_dir / "openapi-schema.json"
    print(f"📝 Génération du schéma OpenAPI JSON : {json_path}")
    call_command("spectacular", "--file", str(json_path), "--format", "openapi-json")
    print(f"✅ Schéma OpenAPI JSON généré : {json_path}")

    # Générer le schéma YAML
    yaml_path = docs_dir / "openapi-schema.yaml"
    print(f"📝 Génération du schéma OpenAPI YAML : {yaml_path}")
    call_command("spectacular", "--file", str(yaml_path), "--format", "openapi")
    print(f"✅ Schéma OpenAPI YAML généré : {yaml_path}")


def convert_openapi_to_postman() -> None:
    """Convertit le schéma OpenAPI en collection Postman."""
    docs_dir = Path(__file__).parent.parent / "docs" / "api"
    openapi_path = docs_dir / "openapi-schema.json"
    postman_path = docs_dir / "postman-collection.json"

    if not openapi_path.exists():
        print("❌ Le schéma OpenAPI n'existe pas. Générez-le d'abord.")
        return

    print("📝 Conversion du schéma OpenAPI en collection Postman...")

    # Charger le schéma OpenAPI
    with open(openapi_path, encoding="utf-8") as f:
        openapi_schema = json.load(f)

    # Créer la collection Postman
    postman_collection = {
        "info": {
            "name": openapi_schema.get("info", {}).get("title", "Kàff GUI API"),
            "description": openapi_schema.get("info", {}).get("description", ""),
            "version": openapi_schema.get("info", {}).get("version", "1.0.0"),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000", "type": "string"},
            {"key": "access_token", "value": "", "type": "string"},
            {"key": "refresh_token", "value": "", "type": "string"},
        ],
        "item": [],
    }

    # Grouper les endpoints par tags
    paths = openapi_schema.get("paths", {})
    tags_map: dict[str, list] = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                tags = details.get("tags", ["default"])
                tag = tags[0] if tags else "default"

                if tag not in tags_map:
                    tags_map[tag] = []

                # Créer la requête Postman
                request = {
                    "name": details.get("summary", f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [
                            {"key": "Content-Type", "value": "application/json"},
                        ],
                        "url": {
                            "raw": "{{base_url}}" + path,
                            "host": ["{{base_url}}"],
                            "path": path.strip("/").split("/"),
                        },
                        "description": details.get("description", ""),
                    },
                }

                # Ajouter le body pour POST/PUT/PATCH
                if method.upper() in ["POST", "PUT", "PATCH"]:
                    request_body = details.get("requestBody", {})
                    if request_body:
                        content = request_body.get("content", {})
                        json_content = content.get("application/json", {})
                        schema = json_content.get("schema", {})
                        example = json_content.get("example", {})

                        request["request"]["body"] = {
                            "mode": "raw",
                            "raw": json.dumps(example or schema, indent=2),
                        }

                tags_map[tag].append(request)

    # Créer les dossiers par tag
    for tag, requests in sorted(tags_map.items()):
        folder = {"name": tag.capitalize(), "item": requests}
        postman_collection["item"].append(folder)

    # Sauvegarder la collection
    with open(postman_path, "w", encoding="utf-8") as f:
        json.dump(postman_collection, f, indent=2, ensure_ascii=False)

    print(f"✅ Collection Postman générée : {postman_path}")
    print("\n📦 Import dans Postman :")
    print("   1. Ouvrir Postman")
    print("   2. File > Import")
    print(f"   3. Sélectionner {postman_path}")
    print("   4. Configurer les variables d'environnement (base_url, access_token)")


def main() -> None:
    """Point d'entrée principal."""
    print("🚀 Génération de la documentation API\n")

    # Générer le schéma OpenAPI
    generate_openapi_schema()

    print()

    # Convertir en collection Postman
    convert_openapi_to_postman()

    print("\n✨ Documentation API générée avec succès !")
    print("\n📚 Fichiers générés :")
    print("   - docs/api/openapi-schema.json")
    print("   - docs/api/openapi-schema.yaml")
    print("   - docs/api/postman-collection.json")
    print("\n🌐 Swagger UI : http://localhost:8000/api/docs/")
    print("📖 Redoc : http://localhost:8000/api/redoc/")


if __name__ == "__main__":
    main()
