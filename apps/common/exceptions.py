"""
Handler d'exception API unifié.

Format de réponse d'erreur (stable côté mobile, validé par Zod):

    {
      "error": {
        "code": "validation_error",
        "message": "Les données fournies sont invalides.",
        "details": { "field_name": ["...message..."] },
        "request_id": "abc-123"
      }
    }
"""

from __future__ import annotations

from typing import Any

import structlog
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = structlog.get_logger(__name__)


class BusinessRuleError(exceptions.APIException):
    """
    Erreur de règle métier (RM-*).

    Utilisée pour signaler une violation d'invariant : tentative de mettre en couple
    deux pigeons du même sexe, supprimer une cage occupée, etc.
    """

    status_code: int = status.HTTP_409_CONFLICT
    default_detail = "Cette opération viole une règle métier."
    default_code = "business_rule_violation"


_EXCEPTION_CODE_MAP: dict[type[Exception], str] = {
    exceptions.AuthenticationFailed: "authentication_failed",
    exceptions.NotAuthenticated: "not_authenticated",
    exceptions.PermissionDenied: "permission_denied",
    exceptions.NotFound: "not_found",
    exceptions.MethodNotAllowed: "method_not_allowed",
    exceptions.Throttled: "throttled",
    exceptions.ValidationError: "validation_error",
    BusinessRuleError: "business_rule_violation",
}


def _resolve_code(exc: Exception) -> str:
    # 1. Préférer l'attribut `default_code` de l'exception (sous-classes spécifiques
    #    comme DecryptionError surchargent ainsi le code parent BusinessRuleError).
    code = getattr(exc, "default_code", None)
    if isinstance(code, str) and code:
        return code
    # 2. Sinon fallback sur la map de classes (matching par isinstance).
    for klass, mapped in _EXCEPTION_CODE_MAP.items():
        if isinstance(exc, klass):
            return mapped
    return "internal_error"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Exception handler DRF normalisé.

    - Convertit les exceptions Django (Http404, PermissionDenied) en réponses DRF.
    - Standardise le format de réponse d'erreur.
    - Trace les 5xx dans les logs structurés.
    """
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)

    if response is None:
        # Erreur non-gérée → 500 (loggée pour analyse)
        logger.exception("unhandled_exception", exc_info=exc, view=context.get("view"))
        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Une erreur inattendue est survenue.",
                    "details": None,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request is not None else None

    payload: dict[str, Any] = {
        "code": _resolve_code(exc),
        "message": _extract_message(response.data),
        "details": response.data if isinstance(response.data, dict | list) else None,
    }
    if request_id is not None:
        payload["request_id"] = request_id

    response.data = {"error": payload}
    return response


def _extract_message(data: Any) -> str:
    """Extrait un message lisible du payload DRF (qui peut être un dict, une liste, un str)."""
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    if isinstance(data, list) and data:
        return str(data[0])
    if isinstance(data, str):
        return data
    return "Erreur de validation."
