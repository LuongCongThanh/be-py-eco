from __future__ import annotations

from rest_framework import serializers


class ExchangeRateSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    base_currency = serializers.CharField()
    target_currency = serializers.CharField()
    rate = serializers.DecimalField(max_digits=20, decimal_places=10)
    # DRF's own `Field.source` attribute (pointing at the model attribute
    # to read) is typed `str | None`; naming our field "source" too is a
    # legitimate name collision with that internal attribute, not a real
    # type error.
    source = serializers.CharField()  # type: ignore[assignment]
    fetched_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    is_stale = serializers.BooleanField()
