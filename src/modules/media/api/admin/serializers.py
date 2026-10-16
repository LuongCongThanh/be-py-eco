from __future__ import annotations

from rest_framework import serializers

from modules.media.services.request_upload import MAX_UPLOAD_SIZE_BYTES


class RequestUploadSerializer(serializers.Serializer):
    content_type = serializers.CharField()
    size_bytes = serializers.IntegerField(min_value=1, max_value=MAX_UPLOAD_SIZE_BYTES)


class UploadCredentialSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    media_upload_id = serializers.UUIDField()
    upload_url = serializers.URLField()
    upload_fields = serializers.DictField()
