from __future__ import annotations

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from modules.catalog.constants import DEFAULT_LOCALE
from modules.pricing.constants import BASE_CURRENCY
from modules.pricing.selectors.price_converter import PriceConverter, get_price_converter
from modules.search.api.storefront.serializers import (
    AutocompleteQuerySerializer,
    ProductDocumentSerializer,
    SearchQuerySerializer,
    SearchResultSerializer,
)
from modules.search.selectors.search_query import build_autocomplete_query, build_search_query
from modules.search.services.execute_search import execute_search

_ALLOWED_LOCALES = ("vi", "en")


def _resolve_locale(request: Request) -> str:
    """Same parsing approach as `localization.services.suggest_locale`
    and `catalog.api.storefront.views`."""
    accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().split("-")[0].lower()
        if lang in _ALLOWED_LOCALES:
            return lang
    return DEFAULT_LOCALE


def _validated_params(serializer_class: type, request: Request) -> dict[str, Any]:
    serializer = serializer_class(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)


def _with_converted_price(hits: list[dict], converter: PriceConverter) -> list[dict]:
    """Re-derives each hit's price from the still-VND `base_price_vnd`
    field rather than trusting anything already baked into the index — an
    already-converted price would go stale the moment the rate changes
    without a reindex.

    The `converter` arrives already bound to a rate, so this loop costs no
    database queries at all, however many hits come back."""
    documents = []
    for hit in hits:
        document = dict(hit)
        price = converter.convert(document.get("base_price_vnd"))
        document["price"] = {
            "amount": price.amount,
            "currency": price.currency,
            "is_stale": price.is_stale,
        }
        documents.append(document)
    return documents


class ProductSearchView(APIView):
    """Full-text, faceted, sortable Product search — guild.md §15 Slice 3,
    commits 3-5. Results are explicitly not authoritative for price or
    availability (Issue #8's Decision Document) — any consumer must
    re-verify at Cart (Slice 4) / Checkout (Slice 5)."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Search published Products",
        parameters=[SearchQuerySerializer],
        responses=SearchResultSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        params = _validated_params(SearchQuerySerializer, request)
        locale = _resolve_locale(request)
        converter = get_price_converter(target_currency=params.get("currency", BASE_CURRENCY))

        # UUIDs are stringified at this boundary: `build_search_query`
        # builds a JSON body, and a UUID in it would have to be coerced
        # eventually anyway — later, and further from where it arrived.
        body = build_search_query(
            text=params.get("q"),
            category_id=str(params["category_id"]) if "category_id" in params else None,
            brand_id=str(params["brand_id"]) if "brand_id" in params else None,
            attribute_value_ids=[str(value) for value in params.get("attribute_value_id", [])]
            or None,
            price_min=params.get("price_min"),
            price_max=params.get("price_max"),
            available_only=params["available_only"],
            sort=params["sort"],
        )

        hits = execute_search(locale=locale, body=body)
        return Response(success_envelope(_with_converted_price(hits, converter), request=request))


class ProductAutocompleteView(APIView):
    """Prefix-match suggestions — guild.md §15 Slice 3, commit 3 /
    Directory Structure (`api/storefront/ # search, autocomplete`)."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Autocomplete Product names",
        parameters=[AutocompleteQuerySerializer],
        responses=ProductDocumentSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        params = _validated_params(AutocompleteQuerySerializer, request)
        locale = _resolve_locale(request)
        body = build_autocomplete_query(params["q"])

        hits = execute_search(locale=locale, body=body)
        return Response(success_envelope(hits, request=request))
