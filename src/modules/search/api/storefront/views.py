from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from modules.catalog.constants import DEFAULT_LOCALE
from modules.pricing.constants import BASE_CURRENCY
from modules.pricing.selectors.get_converted_price import get_converted_price
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


def _with_converted_price(hits: list[dict], currency: str) -> list[dict]:
    """Re-derives each hit's price from the still-VND `base_price_vnd`
    field rather than trusting anything already baked into the index — an
    already-converted price would go stale the moment the rate changes
    without a reindex."""
    documents = []
    for hit in hits:
        document = dict(hit)
        price = get_converted_price(
            base_price_vnd=document.get("base_price_vnd"), target_currency=currency
        )
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

    def get(self, request: Request) -> Response:
        locale = _resolve_locale(request)
        currency = request.query_params.get("currency", BASE_CURRENCY)
        params = request.query_params
        attribute_value_ids = params.getlist("attribute_value_id") or None
        body = build_search_query(
            text=params.get("q"),
            category_id=params.get("category_id"),
            brand_id=params.get("brand_id"),
            attribute_value_ids=attribute_value_ids,
            price_min=int(params["price_min"]) if "price_min" in params else None,
            price_max=int(params["price_max"]) if "price_max" in params else None,
            available_only=params.get("available_only") == "true",
            sort=params.get("sort", "relevance"),
        )

        hits = execute_search(locale=locale, body=body)
        return Response(success_envelope(_with_converted_price(hits, currency), request=request))


class ProductAutocompleteView(APIView):
    """Prefix-match suggestions — guild.md §15 Slice 3, commit 3 /
    Directory Structure (`api/storefront/ # search, autocomplete`)."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        locale = _resolve_locale(request)
        prefix = request.query_params.get("q", "")
        body = build_autocomplete_query(prefix)

        hits = execute_search(locale=locale, body=body)
        return Response(success_envelope(hits, request=request))
