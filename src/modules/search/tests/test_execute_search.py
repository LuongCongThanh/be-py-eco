"""execute_search — the seam every search-facing view must call through
(guild.md §7.6's adapter convention) rather than reaching for
get_opensearch_client() directly, and its Problem-Details error mapping.
"""

from unittest.mock import MagicMock, patch

import pytest
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from modules.search.errors import SearchUnavailableError
from modules.search.services.execute_search import execute_search


def test_returns_the_sources_of_each_hit() -> None:
    fake_client = MagicMock()
    fake_client.search.return_value = {
        "hits": {"hits": [{"_source": {"product_id": "p1"}}, {"_source": {"product_id": "p2"}}]}
    }

    with patch(
        "modules.search.services.execute_search.get_opensearch_client", return_value=fake_client
    ):
        hits = execute_search(locale="vi", body={"query": {"match_all": {}}})

    assert hits == [{"product_id": "p1"}, {"product_id": "p2"}]


def test_cluster_failure_raises_search_unavailable_error() -> None:
    fake_client = MagicMock()
    fake_client.search.side_effect = OpenSearchConnectionError("boom")

    with patch(
        "modules.search.services.execute_search.get_opensearch_client", return_value=fake_client
    ):
        with pytest.raises(SearchUnavailableError):
            execute_search(locale="vi", body={"query": {"match_all": {}}})
