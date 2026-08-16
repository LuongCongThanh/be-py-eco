from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from modules.accounts.models import Staff


class IsStaff(BasePermission):
    """Rejects a validly-authenticated Customer trying to call an admin
    endpoint — JWTAuthentication accepts both actor types, so `IsAuthenticated`
    alone doesn't distinguish them."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return isinstance(request.user, Staff)
