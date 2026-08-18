"""search-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code`, raised from services/views and turned
into Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_502_BAD_GATEWAY


class SearchUnavailableError(APIException):
    status_code = HTTP_502_BAD_GATEWAY
    default_detail = "The search index is temporarily unavailable."
    default_code = "search.unavailable"
