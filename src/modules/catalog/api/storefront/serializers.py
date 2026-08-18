from __future__ import annotations

from rest_framework import serializers


class ProductStorefrontSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    id = serializers.UUIDField()
    name = serializers.CharField(allow_null=True)
    is_name_fallback = serializers.BooleanField()
    base_price_vnd = serializers.IntegerField(
        allow_null=True,
        help_text="Placeholder VND Base Price of the first sellable Variant; currency "
        "conversion lands in Slice 3.",
    )
