"""localization-module business errors — see common/api/exceptions.py for
how these become Problem Details responses.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_503_SERVICE_UNAVAILABLE


class SupportedCountryNotConfiguredError(APIException):
    status_code = HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "No active Supported Country is configured."
    default_code = "localization.supported_country_not_configured"


class UnsupportedLocaleError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "This locale isn't supported by the active Supported Country."
    default_code = "localization.unsupported_locale"


class UnsupportedCurrencyError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "This currency isn't supported by the active Supported Country."
    default_code = "localization.unsupported_currency"
