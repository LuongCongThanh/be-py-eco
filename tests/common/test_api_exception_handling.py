"""API test: the DRF exception handler returns the documented Problem
Details shape (guild.md §5.4) for a deliberately-triggered 404 and 400.
"""

from django.http import Http404
from django.test import Client, override_settings
from django.urls import path
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView


class _NotFoundView(APIView):
    def get(self, request):
        raise Http404


class _ValidationView(APIView):
    def get(self, request):
        raise ValidationError({"quantity": ["Only 2 units are available."]})


urlpatterns = [
    path("not-found/", _NotFoundView.as_view()),
    path("validation/", _ValidationView.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
def test_404_returns_problem_details_shape(client: Client) -> None:
    response = client.get("/not-found/")

    assert response.status_code == 404
    body = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == 404
    assert body["code"] == "not_found"
    assert body["errors"] == []
    assert body["trace_id"]
    assert response["X-Request-ID"] == body["trace_id"]


@override_settings(ROOT_URLCONF=__name__)
def test_400_field_error_returns_problem_details_shape(client: Client) -> None:
    response = client.get("/validation/")

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == 400
    assert body["code"] == "invalid"
    assert body["errors"] == [
        {"field": "quantity.0", "code": "invalid", "message": "Only 2 units are available."}
    ]
