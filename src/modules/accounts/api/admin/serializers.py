from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from modules.accounts.models import Staff


class StaffLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class CreateStaffSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=Staff.Role.choices)

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value


class StaffResponseSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.CharField()


class MfaSetupResponseSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    provisioning_uri = serializers.CharField()


class ConfirmMfaSerializer(serializers.Serializer):
    token = serializers.CharField()


class DisableCustomerSerializer(serializers.Serializer):
    reason = serializers.CharField()
