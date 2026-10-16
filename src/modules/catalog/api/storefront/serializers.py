from __future__ import annotations

from rest_framework import serializers

from common.api.pagination import CursorPageSerializer


class ConvertedPriceSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    amount = serializers.IntegerField(
        allow_null=True,
        help_text="Integer minor-unit amount in `currency`; null if no rate has been "
        "synced for this pair (see is_stale).",
    )
    currency = serializers.CharField()
    is_stale = serializers.BooleanField(
        help_text="True if the required Exchange Rate is missing or expired — the price "
        "display should signal this, per guild.md §15 Slice 3."
    )


class ProductStorefrontSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    id = serializers.UUIDField()
    name = serializers.CharField(allow_null=True)
    is_name_fallback = serializers.BooleanField()
    base_price_vnd = serializers.IntegerField(
        allow_null=True, help_text="The unconverted VND Base Price of the first sellable Variant."
    )
    price = ConvertedPriceSerializer(
        help_text="base_price_vnd converted into the requested `currency` query param "
        "(defaults to VND)."
    )


class ProductListQuerySerializer(CursorPageSerializer):
    """Query params for the Storefront Product listing.

    `currency` is described but not policed here: which currencies a
    Customer may ask for is settled by the Supported Country and then by
    pricing (ADR-0008), further in than the API layer.
    """

    currency = serializers.CharField(
        required=False,
        help_text="Transaction Currency for the returned prices; defaults to the "
        "Customer's preference, then the Supported Country's.",
    )
