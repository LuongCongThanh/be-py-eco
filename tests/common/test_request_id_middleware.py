"""API test: every response carries an `X-Request-ID` header."""

from django.test import Client


def test_request_id_header_is_present_on_every_response(client: Client) -> None:
    response = client.get("/no-such-path/")

    assert response["X-Request-ID"]
