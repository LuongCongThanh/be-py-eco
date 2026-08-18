from __future__ import annotations

from rest_framework import serializers


class LocalizedFieldSerializer(serializers.Serializer):
    """Response shape only — a translated field plus the CMS-visible
    fallback flag (guild.md §15 Slice 2, commit 5)."""

    value = serializers.CharField(allow_null=True)
    locale = serializers.CharField(allow_null=True)
    is_fallback = serializers.BooleanField()


class CategoryDetailSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    id = serializers.UUIDField()
    parent_id = serializers.UUIDField(allow_null=True)
    name = LocalizedFieldSerializer()


class ProductDetailSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    id = serializers.UUIDField()
    status = serializers.CharField()
