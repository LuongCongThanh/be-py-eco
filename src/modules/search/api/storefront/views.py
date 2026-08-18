from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from integrations.opensearch.client import get_opensearch_client
from modules.catalog.constants import DEFAULT_LOCALE
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
        hits = [hit["_source"] for hit in result["hits"]["hits"]]
        return Response(success_envelope(hits, request=request))
