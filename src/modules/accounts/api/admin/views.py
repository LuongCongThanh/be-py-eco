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
from common.api.idempotency import remember_response, replay_if_cached, require_idempotency_key
from common.api.throttling import AuthAccountRateThrottle, AuthIPRateThrottle, AuthUserRateThrottle
from modules.accounts.api.admin.serializers import (
    ConfirmMfaSerializer,
    CreateStaffSerializer,
    DisableCustomerSerializer,
    MfaSetupResponseSerializer,
    StaffLoginSerializer,
    StaffResponseSerializer,
)
from modules.accounts.api.permissions import IsStaff
from modules.accounts.api.storefront.serializers import TokenResponseSerializer
from modules.accounts.models import Staff
from modules.accounts.services.create_staff import create_staff
from modules.accounts.services.disable_customer import disable_customer
from modules.accounts.services.mfa import confirm_mfa_setup, reset_staff_mfa, start_mfa_setup
from modules.accounts.services.staff_login import login_staff


class StaffLoginView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthIPRateThrottle, AuthAccountRateThrottle]

    @extend_schema(
        summary="Log in a staff member",
        description="Authenticates a staff member with email and password, returning access and refresh tokens.",
        request=StaffLoginSerializer,
        responses=TokenResponseSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = StaffLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, access, refresh = login_staff(**serializer.validated_data)
        data = {"access": access, "refresh": refresh}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class CreateStaffView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Create a staff account",
        description=(
            "Creates a new staff account. Requires the acting staff member to have "
            "confirmed MFA and an `Idempotency-Key` header."
        ),
        request=CreateStaffSerializer,
        responses={201: StaffResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        actor = cast(Staff, request.user)
        idempotency_key = require_idempotency_key(request)
        cached = replay_if_cached(
            request=request,
            actor_type="staff",
            actor_id=str(actor.id),
            action="accounts.create_staff",
            idempotency_key=idempotency_key,
        )
        if cached is not None:
            return cached

        serializer = CreateStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = create_staff(actor=actor, request=request, **serializer.validated_data)
        data = {"id": str(staff.id), "email": staff.email, "role": staff.role}
        response = Response(success_envelope(data, request=request), status=status.HTTP_201_CREATED)
        remember_response(
            request=request,
            actor_type="staff",
            actor_id=str(actor.id),
            action="accounts.create_staff",
            idempotency_key=idempotency_key,
            response=response,
        )
        return response


class MfaSetupView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Start MFA setup",
        description="Generates a new TOTP secret and provisioning URI for the authenticated staff member.",
        request=None,
        responses=MfaSetupResponseSerializer,
    )
    def post(self, request: Request) -> Response:
        _, provisioning_uri = start_mfa_setup(staff=cast(Staff, request.user))
        data = {"provisioning_uri": provisioning_uri}
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)


class MfaConfirmView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]
    throttle_classes = [AuthIPRateThrottle, AuthUserRateThrottle]

    @extend_schema(
        summary="Confirm MFA setup",
        description="Verifies a TOTP token to activate MFA for the authenticated staff member.",
        request=ConfirmMfaSerializer,
        responses={204: None},
    )
    def post(self, request: Request) -> Response:
        serializer = ConfirmMfaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirm_mfa_setup(staff=cast(Staff, request.user), token=serializer.validated_data["token"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class DisableCustomerView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Disable a customer account",
        description=(
            "Disables the specified customer account and revokes its sessions. Requires an "
            "audit reason, confirmed MFA on the acting staff member, and an `Idempotency-Key` header."
        ),
        request=DisableCustomerSerializer,
        responses={204: None},
    )
    def post(self, request: Request, customer_id: UUID) -> Response:
        actor = cast(Staff, request.user)
        idempotency_key = require_idempotency_key(request)
        cached = replay_if_cached(
            request=request,
            actor_type="staff",
            actor_id=str(actor.id),
            action="accounts.disable_customer",
            idempotency_key=idempotency_key,
        )
        if cached is not None:
            return cached

        serializer = DisableCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        disable_customer(
            actor=actor,
            customer_id=customer_id,
            reason=serializer.validated_data["reason"],
            request=request,
        )
        response = Response(status=status.HTTP_204_NO_CONTENT)
        remember_response(
            request=request,
            actor_type="staff",
            actor_id=str(actor.id),
            action="accounts.disable_customer",
            idempotency_key=idempotency_key,
            response=response,
        )
        return response


class ResetStaffMfaView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        summary="Reset staff MFA",
        description=(
            "Deletes the target staff member's MFA device, forcing re-enrollment. Requires "
            "confirmed MFA on the acting staff member and an `Idempotency-Key` header."
        ),
        request=None,
        responses={204: None},
    )
    def post(self, request: Request, staff_id: UUID) -> Response:
        actor = cast(Staff, request.user)
        idempotency_key = require_idempotency_key(request)
        cached = replay_if_cached(
            request=request,
            actor_type="staff",
            actor_id=str(actor.id),
            action="accounts.reset_staff_mfa",
            idempotency_key=idempotency_key,
        )
        if cached is not None:
            return cached

        target_staff = Staff.objects.get(id=staff_id)
        reset_staff_mfa(actor=actor, target_staff=target_staff, request=request)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        remember_response(
            request=request,
            actor_type="staff",
            actor_id=str(actor.id),
            action="accounts.reset_staff_mfa",
            idempotency_key=idempotency_key,
            response=response,
        )
        return response
