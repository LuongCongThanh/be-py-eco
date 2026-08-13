from integrations.opensearch.client import get_opensearch_client


def test_opensearch_is_reachable():
    client = get_opensearch_client()
    assert client.ping() is True
