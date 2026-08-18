from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from integrations.opensearch.client import get_opensearch_client
from modules.catalog.constants import DEFAULT_LOCALE
from modules.pricing.constants import BASE_CURRENCY
from modules.pricing.selectors.get_converted_price import get_converted_price
from modules.search.mapping import index_name
from modules.search.selectors.search_query import build_search_query

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

        client = get_opensearch_client()
        result = client.search(index=index_name(locale), body=body)
        hits = []
        for hit in result["hits"]["hits"]:
            document = dict(hit["_source"])
            # Search-result prices are re-derived from the still-VND
            # base_price_vnd field, never trusted as already-converted —
            # this is the same conversion path Product detail uses, kept
            # here rather than baked into the index (an already-converted
            # price would go stale the moment the rate changes without a
            # reindex).
            price = get_converted_price(
                base_price_vnd=document.get("base_price_vnd"), target_currency=currency
            )
            document["price"] = {
                "amount": price.amount,
                "currency": price.currency,
                "is_stale": price.is_stale,
            }
            hits.append(document)
        return Response(success_envelope(hits, request=request))
