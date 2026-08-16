from __future__ import annotations

from rest_framework import serializers


class LocaleSuggestionResponseSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    country_code = serializers.CharField()
    locale = serializers.CharField()
    currency = serializers.CharField()
