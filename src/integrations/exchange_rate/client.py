"""Exchange rate provider adapter (guild.md §7.6 / §15 Slice 3, commit 7):
`pricing.services.sync_exchange_rates` never calls a vendor SDK directly —
it goes through this interface, and the concrete implementation is chosen
via `settings.EXCHANGE_RATE_PROVIDER_CLASS`.

The production adapter is an explicit pending decision (`guild.md` §16 —
"production exchange-rate provider"), not implemented here; only the
interface and a deterministic fake exist, so later slices (and
eventually a real provider) plug in without changing calling code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from django.conf import settings
from django.utils.module_loading import import_string


class ExchangeRateProviderError(Exception):
    """Raised when a rate can't be fetched from the provider."""


@dataclass(frozen=True)
class Rate:
    base_currency: str
    target_currency: str
    rate: Decimal
    source: str
    fetched_at: datetime


class ExchangeRateProvider(Protocol):
    def get_rate(self, base_currency: str, target_currency: str) -> Rate: ...


def get_exchange_rate_provider() -> ExchangeRateProvider:
    provider_class = import_string(settings.EXCHANGE_RATE_PROVIDER_CLASS)
    return provider_class()  # type: ignore[no-any-return]
