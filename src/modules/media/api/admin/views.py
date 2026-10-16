from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from common.api.schema import enveloped
from modules.accounts.api.permissions import IsStaff
from modules.media.api.admin.serializers import RequestUploadSerializer, UploadCredentialSerializer
from modules.media.services.request_upload import request_upload


class RequestUploadView(APIView):
    """Admin CMS requests a short-lived presigned upload credential —
    guild.md §15 Slice 2, commit 8. The Admin CMS never holds storage
    credentials of its own; it uploads directly to S3-compatible storage
    with this credential, never proxying the file body through Django."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Request a presigned media upload credential",
        request=RequestUploadSerializer,
        responses=enveloped(UploadCredentialSerializer),
    )
    def post(self, request: Request) -> Response:
        serializer = RequestUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credential = request_upload(**serializer.validated_data)
        data = {
            "media_upload_id": credential.media_upload.id,
            "upload_url": credential.upload_url,
            "upload_fields": credential.upload_fields,
        }
        return Response(success_envelope(data, request=request))
