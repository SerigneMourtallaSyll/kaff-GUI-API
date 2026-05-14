#!/usr/bin/env python
"""Point d'entrée Django pour les commandes administratives."""

from __future__ import annotations

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django n'a pas pu être importé. Vérifiez que l'environnement virtuel "
            "est activé (uv sync && .venv\\Scripts\\activate) et que Django est installé."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
