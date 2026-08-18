from __future__ import annotations

from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer):
    """Request query-params only — used for OpenAPI docs, not validation
    (query params are read directly off `request.query_params`)."""

    q = serializers.CharField(required=False)
    category_id = serializers.CharField(required=False)
    brand_id = serializers.CharField(required=False)
    price_min = serializers.IntegerField(required=False)
    price_max = serializers.IntegerField(required=False)
    available_only = serializers.BooleanField(required=False)
    sort = serializers.ChoiceField(
        choices=["relevance", "popularity", "rating", "recency"], required=False
    )


class SearchResultSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    product_id = serializers.UUIDField()
    name = serializers.CharField()
    base_price_vnd = serializers.IntegerField(allow_null=True)
    is_available = serializers.BooleanField()
