"""translation-module business errors — DRF `APIException` subclasses with
a stable, dotted `default_code`, raised from services and turned into
Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_404_NOT_FOUND


class TranslationEntryNotFoundError(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "Translation entry not found."
    default_code = "translation.entry_not_found"
