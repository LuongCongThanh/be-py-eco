from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.envelope import success_envelope
from modules.localization.api.storefront.serializers import LocaleSuggestionResponseSerializer
from modules.localization.services.suggest_locale import suggest_locale


class LocaleSuggestionView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Suggest locale",
        description=(
            "Suggests a locale, country, and currency for the request based on its IP "
            "address/headers."
        ),
        request=None,
        responses=LocaleSuggestionResponseSerializer,
    )
    def get(self, request: Request) -> Response:
        suggestion = suggest_locale(request._request)
        data = {
            "country_code": suggestion.country_code,
            "locale": suggestion.locale,
            "currency": suggestion.currency,
        }
        return Response(success_envelope(data, request=request), status=status.HTTP_200_OK)
