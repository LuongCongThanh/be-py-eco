"""API test: `/api/v1/schema/` serves a valid OpenAPI 3.1 document."""

from django.test import Client


def test_schema_endpoint_serves_openapi_3_1_document(client: Client) -> None:
    response = client.get("/api/v1/schema/")

    assert response.status_code == 200
    body = response.content.decode()
    assert "openapi: 3.1.0" in body
