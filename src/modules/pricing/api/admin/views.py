from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from common.api.schema import enveloped
from modules.accounts.api.permissions import IsStaff
from modules.pricing.api.admin.serializers import ExchangeRateSerializer
from modules.pricing.constants import BASE_CURRENCY, SUPPORTED_TARGET_CURRENCIES
from modules.pricing.selectors.get_latest_rate import get_latest_rate


class ExchangeRateListView(APIView):
    """A Store Manager views the current Exchange Rate for every
    configured Transaction Currency, including source/timestamp/expiry —
    guild.md §15 Slice 3's acceptance criteria. Read-only: rates sync on
    Celery Beat's schedule (`pricing.tasks.sync_exchange_rates`), never
    on-demand from this endpoint."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        operation_id="admin_pricing_exchange_rates_list",
        summary="List current Exchange Rates",
        responses=enveloped(ExchangeRateSerializer, many=True),
    )
    def get(self, request: Request) -> Response:
        data = []
        for target_currency in SUPPORTED_TARGET_CURRENCIES:
            rate = get_latest_rate(base_currency=BASE_CURRENCY, target_currency=target_currency)
            if rate is None:
                continue
            data.append(
                {
                    "base_currency": rate.base_currency,
                    "target_currency": rate.target_currency,
                    "rate": rate.rate,
                    "source": rate.source,
                    "fetched_at": rate.fetched_at,
                    "expires_at": rate.expires_at,
                    "is_stale": rate.is_stale,
                }
            )
        return Response(success_envelope(data, request=request))
