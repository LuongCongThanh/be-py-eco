"""pricing-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code`, raised from services and turned into
Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST


class UnsupportedCurrencyError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "This currency has no configured minor-unit exponent."
    default_code = "pricing.unsupported_currency"
