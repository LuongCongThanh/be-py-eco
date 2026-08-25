from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from common.api.pagination import (
    decode_cursor,
    encode_cursor,
    pagination_meta,
    query_fingerprint,
)
from common.api.schema import enveloped
from modules.catalog.api.storefront.serializers import (
    ProductListQuerySerializer,
    ProductStorefrontSerializer,
)
from modules.catalog.constants import DEFAULT_LOCALE
from modules.catalog.errors import ProductNotFoundError
from modules.catalog.models.product import Product, ProductStatus
from modules.localization.services.resolve_storefront_context import (
    resolve_storefront_context,
)
from modules.pricing.selectors.price_converter import PriceConverter, get_price_converter
from modules.translation.selectors.get_localized_field import get_localized_field


def _serialize_product(
    product: Product, locale: str, converter: PriceConverter
) -> tuple[dict, str]:
    """Takes an already-built `converter` rather than a currency string so
    the list path resolves the Exchange Rate once, not once per Product."""
    name = get_localized_field(product, field="name", locale=locale, default_locale=DEFAULT_LOCALE)
    first_variant = product.variants.filter(is_archived=False).order_by("created_at").first()
    base_price_vnd = first_variant.base_price_vnd if first_variant else None
    price = converter.convert(base_price_vnd)
    data = {
        "id": product.id,
        "name": name.value,
        "is_name_fallback": name.is_fallback,
        "base_price_vnd": base_price_vnd,
        "price": {
            "amount": price.amount,
            "currency": price.currency,
            "is_stale": price.is_stale,
        },
    }
    return data, (name.locale or locale)


class ProductListView(APIView):
    """Published-only, locale-aware Product listing — guild.md §15 Slice
    2, commit 13. Search/discovery filtering is Slice 3's job; this
    endpoint only proves the published-only + localized read path."""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="storefront_catalog_products_list",
        summary="List published Products",
        parameters=[ProductListQuerySerializer],
        responses=enveloped(ProductStorefrontSerializer, many=True, paginated=True),
    )
    def get(self, request: Request) -> Response:
        params = ProductListQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        page_size = params.validated_data["page_size"]

        context = resolve_storefront_context(request)
        converter = get_price_converter(target_currency=context.currency)

        # Keyset on the primary key: it is a UUIDv7, so it is unique *and*
        # time-ordered, which makes it a total order needing no extra index
        # -- ordering by created_at would need a composite one. Products
        # created inside the same millisecond therefore order by the UUID's
        # random bits rather than by creation instant; stable across pages,
        # which is what a cursor requires.
        products = Product.objects.filter(status=ProductStatus.ACTIVE).order_by("id")
        # The listing has no filters yet, so the fingerprint is constant.
        # It is computed anyway so that adding one cannot silently leave
        # old cursors valid against a different result set.
        fingerprint = query_fingerprint({})
        if "cursor" in params.validated_data:
            after = decode_cursor(params.validated_data["cursor"], fingerprint=fingerprint)
            products = products.filter(id__gt=after)

        # One more than asked for: the extra row is how we know whether a
        # further page exists, without a second count query.
        rows = list(products[: page_size + 1])
        has_more = len(rows) > page_size
        rows = rows[:page_size]

        data = [_serialize_product(product, context.locale, converter)[0] for product in rows]
        response = Response(
            success_envelope(
                data,
                request=request,
                pagination=pagination_meta(
                    next_cursor=(
                        encode_cursor(str(rows[-1].id), fingerprint=fingerprint)
                        if has_more
                        else None
                    ),
                    has_more=has_more,
                    page_size=page_size,
                ),
            )
        )
        # A list can mix locales, so no per-Product answer is right. The
        # locale that was *asked for* is the only honest thing to report --
        # previously this reflected whichever Product happened to be last.
        response["Content-Language"] = context.locale
        return response


class ProductDetailView(APIView):
    """Published-only, locale-aware Product detail — guild.md §15 Slice 2,
    commit 13. A `draft` Product 404s here even though it's visible on
    the Admin endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="storefront_catalog_products_retrieve",
        summary="Get a published Product",
        responses=enveloped(ProductStorefrontSerializer),
    )
    def get(self, request: Request, product_id: UUID) -> Response:
        try:
            product = Product.objects.get(pk=product_id, status=ProductStatus.ACTIVE)
        except Product.DoesNotExist as exc:
            raise ProductNotFoundError() from exc

        context = resolve_storefront_context(request)
        converter = get_price_converter(target_currency=context.currency)
        data, response_locale = _serialize_product(product, context.locale, converter)
        response = Response(success_envelope(data, request=request))
        response["Content-Language"] = response_locale
        return response
