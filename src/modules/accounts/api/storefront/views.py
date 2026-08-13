from __future__ import annotations

from typing import cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from modules.accounts.api.storefront.serializers import (
    CustomerResponseSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    SessionResponseSerializer,
    TokenResponseSerializer,
    VerifyEmailSerializer,
)
from modules.accounts.models import Customer, Session
from modules.accounts.services.login_customer import login_customer
from modules.accounts.services.login_with_google import login_with_google
from modules.accounts.services.register_customer import register_customer
from modules.accounts.services.sessions import (
    revoke_all_sessions,
    revoke_session,
    rotate_refresh_token,
)
from modules.accounts.services.verify_email import verify_email


def _customer_representation(customer: Customer) -> dict:
    return {
        "id": str(customer.id),
        "email": customer.email,
        "email_verified": customer.is_email_verified,
    }


class RegisterView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: CustomerResponseSerializer})
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = register_customer(**serializer.validated_data)
        data = _customer_representation(result.customer)
        return Response(success_envelope(data, request=request), status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(request=VerifyEmailSerializer, responses=CustomerResponseSerializer)
    def post(self, request: Request) -> Response:
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = verify_email(raw_token=serializer.validated_data["token"])
        data = _customer_representation(customer)
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class LoginView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses=TokenResponseSerializer)
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, access, refresh = login_customer(**serializer.validated_data)
        data = {"access": access, "refresh": refresh}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(request=GoogleLoginSerializer, responses=TokenResponseSerializer)
    def post(self, request: Request) -> Response:
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, access, refresh = login_with_google(**serializer.validated_data)
        data = {"access": access, "refresh": refresh}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(request=RefreshTokenSerializer, responses=TokenResponseSerializer)
    def post(self, request: Request) -> Response:
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access, refresh = rotate_refresh_token(
            raw_refresh_token=serializer.validated_data["refresh"]
        )
        data = {"access": access, "refresh": refresh}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CustomerResponseSerializer)
    def get(self, request: Request) -> Response:
        data = _customer_representation(cast(Customer, request.user))
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SessionResponseSerializer(many=True))
    def get(self, request: Request) -> Response:
        customer = cast(Customer, request.user)
        sessions = Session.objects.filter(customer=customer, revoked_at__isnull=True).order_by(
            "-created_at"
        )
        data = [
            {"id": str(s.id), "created_at": s.created_at, "expires_at": s.expires_at}
            for s in sessions
            if s.is_active
        ]
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class SessionRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request: Request, session_id: UUID) -> Response:
        revoke_session(customer=cast(Customer, request.user), session_id=session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionRevokeAllView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        revoke_all_sessions(customer=cast(Customer, request.user))
        return Response(status=status.HTTP_204_NO_CONTENT)
