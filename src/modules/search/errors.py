"""search-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code`, raised from services/views and turned
into Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_502_BAD_GATEWAY


class SearchUnavailableError(APIException):
    status_code = HTTP_502_BAD_GATEWAY
    default_detail = "The search index is temporarily unavailable."
    default_code = "search.unavailable"


class SearchIndexMappingDriftError(Exception):
    """The live index's mapping is not the one this code expects.

    Deliberately not an APIException: it is raised while *writing* the
    projection (`index_product`, `reindex_all`), never while serving a
    request, so there is no response for it to shape.

    Its job is to convert a silent wrong answer into a loud one. Without
    it, deploying a mapping change and forgetting to reindex leaves the old
    mapping in place; OpenSearch then dynamically maps new fields as
    analysed text, term filters stop matching, and facets return nothing
    with no indication why -- which looks exactly like the bug the facet
    work was meant to fix.
    """
