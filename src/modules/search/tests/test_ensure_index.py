"""ensure_index — creation, and its refusal to write into a stale mapping.

Runs without a cluster: the client is mocked, because what is being tested
is the decision ensure_index makes about a mapping, not OpenSearch's
behaviour.
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.search.errors import SearchIndexMappingDriftError
from modules.search.mapping import build_index_mapping
from modules.search.services.ensure_index import ensure_index

CLIENT = "modules.search.services.ensure_index.get_opensearch_client"


def _client(*, exists: bool, live_mapping: dict | None = None) -> MagicMock:
    client = MagicMock()
    client.indices.exists.return_value = exists
    if live_mapping is not None:
        client.indices.get_mapping.return_value = {"products_vi": {"mappings": live_mapping}}
    return client


def test_a_missing_index_is_created_with_the_current_mapping() -> None:
    client = _client(exists=False)

    with patch(CLIENT, return_value=client):
        assert ensure_index("vi") == "products_vi"

    body = client.indices.create.call_args.kwargs["body"]
    assert body["mappings"] == build_index_mapping()


def test_an_index_with_the_current_mapping_is_left_alone() -> None:
    client = _client(exists=True, live_mapping=build_index_mapping())

    with patch(CLIENT, return_value=client):
        assert ensure_index("vi") == "products_vi"

    client.indices.create.assert_not_called()


def test_a_stale_mapping_is_refused_rather_than_written_into() -> None:
    """Deploying a mapping change and skipping the reindex used to leave the
    old mapping in place. OpenSearch would then map the new field
    dynamically as analysed text, term filters would stop matching, and
    facets would return nothing with no indication why."""
    stale = {"properties": {"product_id": {"type": "keyword"}}}
    client = _client(exists=True, live_mapping=stale)

    with patch(CLIENT, return_value=client):
        with pytest.raises(SearchIndexMappingDriftError) as raised:
            ensure_index("vi")

    assert "reindex_search" in str(raised.value), "the error must name its own fix"


def test_the_drift_error_names_the_fields_that_differ() -> None:
    """An operator reading this in a Celery log should not have to diff two
    mappings by hand."""
    live = {**build_index_mapping()}
    live["properties"] = {**live["properties"]}
    del live["properties"]["attributes"]
    live["properties"]["attribute_value_ids"] = {"type": "keyword"}
    client = _client(exists=True, live_mapping=live)

    with patch(CLIENT, return_value=client):
        with pytest.raises(SearchIndexMappingDriftError) as raised:
            ensure_index("vi")

    message = str(raised.value)
    assert "attributes" in message
    assert "attribute_value_ids" in message
