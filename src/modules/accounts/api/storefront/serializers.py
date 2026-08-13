from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from modules.accounts.models import Customer


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if Customer.objects.filter(email=normalized).exists():
            raise serializers.ValidationError(
                "A customer with this email already exists.", code="email_taken"
            )
        return normalized

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class CustomerResponseSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    email_verified = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class TokenResponseSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation."""

    access = serializers.CharField()
    refresh = serializers.CharField()
