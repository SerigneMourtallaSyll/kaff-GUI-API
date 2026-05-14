"""Permissions DRF transverses — OWASP A01 : Broken Access Control."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import permissions

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    """
    Autorise l'accès uniquement si l'objet appartient à l'utilisateur authentifié.

    Le modèle DOIT exposer un champ ``user`` (FK vers users.User) sinon adapter
    l'attribut ``owner_field`` au niveau de la vue.
    """

    owner_field = "user"

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        owner_field = getattr(view, "owner_field", self.owner_field)
        owner = getattr(obj, owner_field, None)
        return bool(owner is not None and owner == request.user)


class IsOwnerOrReadOnly(IsOwner):
    """Autorise la lecture publique, l'écriture seulement au propriétaire."""

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_object_permission(request, view, obj)
