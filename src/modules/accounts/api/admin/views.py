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
from common.api.throttling import AuthAccountRateThrottle, AuthIPRateThrottle, AuthUserRateThrottle
from modules.accounts.api.admin.serializers import (
    ConfirmMfaSerializer,
    CreateStaffSerializer,
    MfaSetupResponseSerializer,
    StaffLoginSerializer,
    StaffResponseSerializer,
)
from modules.accounts.api.permissions import IsStaff
from modules.accounts.api.storefront.serializers import TokenResponseSerializer
from modules.accounts.models import Staff
from modules.accounts.services.create_staff import create_staff
from modules.accounts.services.disable_customer import disable_customer
from modules.accounts.services.mfa import confirm_mfa_setup, start_mfa_setup
from modules.accounts.services.staff_login import login_staff


class StaffLoginView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthIPRateThrottle, AuthAccountRateThrottle]

    @extend_schema(request=StaffLoginSerializer, responses=TokenResponseSerializer)
    def post(self, request: Request) -> Response:
        serializer = StaffLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, access, refresh = login_staff(**serializer.validated_data)
        data = {"access": access, "refresh": refresh}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class CreateStaffView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=CreateStaffSerializer, responses={201: StaffResponseSerializer})
    def post(self, request: Request) -> Response:
        serializer = CreateStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = create_staff(actor=cast(Staff, request.user), **serializer.validated_data)
        data = {"id": str(staff.id), "email": staff.email, "role": staff.role}
        return Response(success_envelope(data, request=request), status=status.HTTP_201_CREATED)


class MfaSetupView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=None, responses=MfaSetupResponseSerializer)
    def post(self, request: Request) -> Response:
        _, provisioning_uri = start_mfa_setup(staff=cast(Staff, request.user))
        data = {"provisioning_uri": provisioning_uri}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class MfaConfirmView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]
    throttle_classes = [AuthIPRateThrottle, AuthUserRateThrottle]

    @extend_schema(request=ConfirmMfaSerializer, responses={204: None})
    def post(self, request: Request) -> Response:
        serializer = ConfirmMfaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirm_mfa_setup(staff=cast(Staff, request.user), token=serializer.validated_data["token"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class DisableCustomerView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=None, responses={204: None})
    def post(self, request: Request, customer_id: UUID) -> Response:
        disable_customer(actor=cast(Staff, request.user), customer_id=customer_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
