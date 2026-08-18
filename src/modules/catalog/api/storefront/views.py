from __future__ import annotations

from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from modules.catalog.api.storefront.serializers import ProductStorefrontSerializer
from modules.catalog.constants import DEFAULT_LOCALE
from modules.catalog.errors import ProductNotFoundError
from modules.catalog.models.product import Product, ProductStatus
from modules.pricing.constants import BASE_CURRENCY
from modules.pricing.selectors.get_converted_price import get_converted_price
from modules.translation.selectors.get_localized_field import get_localized_field

_ALLOWED_LOCALES = ("vi", "en")


def _resolve_locale(request: Request) -> str:
    """Best `Accept-Language` match against `_ALLOWED_LOCALES`, falling
    back to `DEFAULT_LOCALE` — same parsing approach as
    `localization.services.suggest_locale`."""
    accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().split("-")[0].lower()
        if lang in _ALLOWED_LOCALES:
            return lang
    return DEFAULT_LOCALE


def _serialize_product(product: Product, locale: str, currency: str) -> tuple[dict, str]:
    name = get_localized_field(product, field="name", locale=locale, default_locale=DEFAULT_LOCALE)
    first_variant = product.variants.filter(is_archived=False).order_by("created_at").first()
    base_price_vnd = first_variant.base_price_vnd if first_variant else None
    price = get_converted_price(base_price_vnd=base_price_vnd, target_currency=currency)
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
        summary="List published Products",
        responses=ProductStorefrontSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        locale = _resolve_locale(request)
        currency = request.query_params.get("currency", BASE_CURRENCY)
        products = Product.objects.filter(status=ProductStatus.ACTIVE).order_by("created_at")
        data = []
        response_locale = locale
        for product in products:
            item, response_locale = _serialize_product(product, locale, currency)
            data.append(item)
        response = Response(success_envelope(data, request=request))
        response["Content-Language"] = response_locale
        return response


class ProductDetailView(APIView):
    """Published-only, locale-aware Product detail — guild.md §15 Slice 2,
    commit 13. A `draft` Product 404s here even though it's visible on
    the Admin endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get a published Product",
        responses=ProductStorefrontSerializer,
    )
    def get(self, request: Request, product_id: UUID) -> Response:
        try:
            product = Product.objects.get(pk=product_id, status=ProductStatus.ACTIVE)
        except Product.DoesNotExist as exc:
            raise ProductNotFoundError() from exc

        locale = _resolve_locale(request)
        currency = request.query_params.get("currency", BASE_CURRENCY)
        data, response_locale = _serialize_product(product, locale, currency)
        response = Response(success_envelope(data, request=request))
        response["Content-Language"] = response_locale
        return response
