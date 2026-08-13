"""Unit test: the success envelope builder matches guild.md §5.3's shape."""

from django.test import RequestFactory

from common.api.envelope import success_envelope
from common.ids.uuid7 import uuid7


def test_success_envelope_includes_request_id() -> None:
    request = RequestFactory().get("/")
    request.id = uuid7()  # type: ignore[attr-defined]

    body = success_envelope({"id": "abc"}, request=request)

    assert body == {"data": {"id": "abc"}, "meta": {"request_id": str(request.id)}}  # type: ignore[attr-defined]


def test_success_envelope_includes_pagination_when_given() -> None:
    body = success_envelope([], pagination={"has_more": False})

    assert body["meta"]["pagination"] == {"has_more": False}


def test_success_envelope_without_request_has_empty_request_id() -> None:
    body = success_envelope({"id": "abc"})

    assert body["meta"]["request_id"] == ""
