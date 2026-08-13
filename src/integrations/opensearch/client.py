"""Thin factory for an opensearch-py client, configured from the environment.

No Django app wraps OpenSearch directly (unlike MinIO, which goes through
django-storages) — the `search` module (Slice 3) will build on this factory.
"""

import environ
from opensearchpy import OpenSearch

env = environ.Env()


def get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[env("OPENSEARCH_URL", default="http://localhost:9200")],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )
