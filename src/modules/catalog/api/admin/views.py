from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from modules.accounts.api.permissions import IsStaff
from modules.catalog.api.admin.serializers import CategoryDetailSerializer
from modules.catalog.errors import CategoryNotFoundError
from modules.catalog.models.category import Category
from modules.translation.selectors.get_localized_field import get_localized_field

# guild.md §2 — launch is Vietnam-only; `vi` is the default locale a
# missing translation falls back to. Slice 11 makes this configurable
# per Supported Country instead of a module constant.
DEFAULT_LOCALE = "vi"


class CategoryDetailView(APIView):
    """Admin read of a single Category, with its translated name and the
    CMS-visible fallback flag — guild.md §15 Slice 2, commit 5's verify
    criterion."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Get a Category",
        description=(
            "Returns a Category's translated name for the requested locale, falling back to "
            "the default locale (with `is_fallback: true`) when no translation exists for it."
        ),
        responses=CategoryDetailSerializer,
    )
    def get(self, request: Request, category_id: UUID) -> Response:
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist as exc:
            raise CategoryNotFoundError() from exc

        locale = request.query_params.get("locale", DEFAULT_LOCALE)
        name = get_localized_field(
            category, field="name", locale=locale, default_locale=DEFAULT_LOCALE
        )
        data = {
            "id": category.id,
            "parent_id": category.parent_id,
            "name": {
                "value": name.value,
                "locale": name.locale,
                "is_fallback": name.is_fallback,
            },
        }
        return Response(success_envelope(data, request=request))
