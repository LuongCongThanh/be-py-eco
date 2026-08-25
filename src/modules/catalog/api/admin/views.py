from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from common.api.schema import enveloped
from modules.accounts.api.permissions import IsStaff
from modules.catalog.api.admin.serializers import CategoryDetailSerializer, ProductDetailSerializer
from modules.catalog.constants import DEFAULT_LOCALE
from modules.catalog.errors import CategoryNotFoundError, ProductNotFoundError
from modules.catalog.models.category import Category
from modules.catalog.models.product import Product
from modules.catalog.services.publish_product import publish_product
from modules.translation.selectors.get_localized_field import get_localized_field


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
        responses=enveloped(CategoryDetailSerializer),
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


class ProductPublishView(APIView):
    """`publish` is a dedicated action, not a generic `PATCH status` —
    guild.md §15 Slice 2, commit 7. Fails with a specific error code per
    missing precondition; the media-readiness check is a stub until
    commit 12 wires the real `media` module in."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Publish a Product",
        description=(
            "Transitions a Product to active. Fails with 409 and a precondition-specific "
            "error code if default-locale content is incomplete, there's no sellable "
            "Variant, or no ready media asset exists."
        ),
        request=None,
        responses=enveloped(ProductDetailSerializer),
    )
    def post(self, request: Request, product_id: UUID) -> Response:
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist as exc:
            raise ProductNotFoundError() from exc

        publish_product(product=product)
        data = {"id": product.id, "status": product.status}
        return Response(success_envelope(data, request=request))
