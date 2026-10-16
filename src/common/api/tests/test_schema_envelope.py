"""Every documented success response must describe the envelope it is
actually sent in.

This is the invariant `enveloped()` exists for, checked against the
*generated* schema rather than against call sites. That matters: the
explicit-helper approach was chosen over a spectacular postprocessing hook
because a hook makes the view and its schema disagree textually, but a
hook had one real advantage -- it cannot be forgotten on the thirtieth
view. This test buys that advantage back without the action at a distance.
"""

from typing import Any

import pytest
import yaml
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    import io

    buffer = io.StringIO()
    call_command("spectacular", stdout=buffer)
    return yaml.safe_load(buffer.getvalue())


def _resolve(schema: dict[str, Any], ref_or_name: str) -> dict[str, Any]:
    """Accepts a `$ref` or a bare component name."""
    return schema["components"]["schemas"][ref_or_name.rsplit("/", 1)[-1]]


def _documented_success_bodies(schema: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    found = []
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            for code, response in operation.get("responses", {}).items():
                content = response.get("content")
                if not code.startswith("2") or not content:
                    continue  # 204/202 carry no body: nothing to envelope.
                found.append((f"{method.upper()} {path}", code, content["application/json"]))
    return found


def test_there_are_documented_success_bodies_to_check(schema) -> None:
    """Guards the guard: a schema that stopped describing any body would
    make every assertion below vacuously pass."""
    assert len(_documented_success_bodies(schema)) >= 20


def test_every_documented_success_body_is_enveloped(schema) -> None:
    offenders = []
    for endpoint, code, media in _documented_success_bodies(schema):
        body = media["schema"]
        if "$ref" in body:
            body = _resolve(schema, body["$ref"])
        if set(body.get("properties", {})) < {"data", "meta"}:
            offenders.append(f"{endpoint} -> {code}")

    assert offenders == [], (
        "these responses do not declare the {data, meta} envelope they are "
        f"actually sent in: {offenders}"
    )


def test_only_paginated_endpoints_promise_pagination(schema) -> None:
    """A schema that promised meta.pagination everywhere would be wrong in
    the opposite direction."""
    paginated = set()
    for endpoint, _code, media in _documented_success_bodies(schema):
        body = media["schema"]
        if "$ref" in body:
            body = _resolve(schema, body["$ref"])
        meta = body.get("properties", {}).get("meta", {})
        if "$ref" in meta and "pagination" in _resolve(schema, meta["$ref"]).get("properties", {}):
            paginated.add(endpoint)

    assert paginated == {
        "GET /api/v1/storefront/catalog/products",
        "GET /api/v1/storefront/search/products/search",
    }


@pytest.mark.django_db
def test_a_real_response_has_the_keys_the_schema_promises(schema, supported_country) -> None:
    """The schema is only worth trusting if it matches a live response."""
    body = APIClient().get("/api/v1/storefront/catalog/products").json()
    declared = _resolve(schema, "EnvelopedProductStorefrontListPage")

    assert set(body) == set(declared["properties"])
    assert set(body["meta"]) == set(_resolve(schema, "PaginatedMeta")["properties"])
