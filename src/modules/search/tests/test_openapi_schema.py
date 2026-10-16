"""The committed API contract must actually generate.

This runs exactly what CI runs (`.github/workflows/ci.yml`): schema
generation with `--validate --fail-on-warn`. Both search views used to
fail it — they had no `extend_schema` and no serializer_class, so
drf-spectacular could not describe them and dropped them from the schema
entirely.
"""

import pytest
from django.core.management import call_command


def test_schema_generates_without_warnings_or_errors(tmp_path) -> None:
    output = tmp_path / "openapi.yaml"

    call_command("spectacular", file=str(output), validate=True, fail_on_warn=True)

    assert output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/storefront/search/products/search",
        "/api/v1/storefront/search/products/autocomplete",
    ],
)
def test_search_endpoints_appear_in_the_schema(tmp_path, path: str) -> None:
    output = tmp_path / "openapi.yaml"

    call_command("spectacular", file=str(output))

    assert path in output.read_text(encoding="utf-8")
