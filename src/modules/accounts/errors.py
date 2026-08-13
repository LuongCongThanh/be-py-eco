"""accounts-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code` (guild.md §5.4's `code` field), raised from
services and turned into Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED


class InvalidVerificationTokenError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired verification token."
    default_code = "accounts.invalid_verification_token"


class InvalidCredentialsError(APIException):
    status_code = HTTP_401_UNAUTHORIZED
    default_detail = "Invalid email or password."
    default_code = "accounts.invalid_credentials"
