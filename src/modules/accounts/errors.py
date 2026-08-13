"""accounts-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code` (guild.md §5.4's `code` field), raised from
services and turned into Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)


class InvalidVerificationTokenError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired verification token."
    default_code = "accounts.invalid_verification_token"


class InvalidCredentialsError(APIException):
    status_code = HTTP_401_UNAUTHORIZED
    default_detail = "Invalid email or password."
    default_code = "accounts.invalid_credentials"


class InvalidRefreshTokenError(APIException):
    status_code = HTTP_401_UNAUTHORIZED
    default_detail = "Invalid, expired or already-used refresh token."
    default_code = "accounts.invalid_refresh_token"


class SessionNotFoundError(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "Session not found."
    default_code = "accounts.session_not_found"


class InvalidGoogleTokenError(APIException):
    status_code = HTTP_401_UNAUTHORIZED
    default_detail = "Invalid or unverifiable Google ID token."
    default_code = "accounts.invalid_google_token"


class EmailAlreadyTakenError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = "This email is already used by another account."
    default_code = "accounts.email_already_taken"


class InsufficientPermissionError(APIException):
    status_code = HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "accounts.insufficient_permission"


class MfaNotConfiguredError(APIException):
    status_code = HTTP_403_FORBIDDEN
    default_detail = "Multi-factor authentication must be set up before performing this action."
    default_code = "accounts.mfa_not_configured"


class InvalidMfaTokenError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "Invalid MFA token."
    default_code = "accounts.invalid_mfa_token"
