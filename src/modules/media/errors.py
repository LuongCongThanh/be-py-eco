"""media-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code`, raised from services and turned into
Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


class MediaUploadNotFoundError(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "Media upload not found."
    default_code = "media.upload_not_found"


class MediaUploadNotReadyError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "Only a ready media upload can be attached to a Product."
    default_code = "media.upload_not_ready"
