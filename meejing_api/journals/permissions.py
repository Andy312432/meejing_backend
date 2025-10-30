from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.models import VisibilityChoices
from social.services import are_users_connected


class IsAuthorOrViewerAllowed(BasePermission):
    """
    Allows authors to manage their entries while applying visibility rules
    for other viewers. Friends-only access is delegated to the social layer.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj: Any) -> bool:
        if request.user and request.user == obj.author:
            return True

        if request.method not in SAFE_METHODS:
            return False

        if obj.visibility == VisibilityChoices.PUBLIC:
            return True

        if obj.visibility == VisibilityChoices.FRIENDS:
            return are_users_connected(request.user, obj.author)

        return False

