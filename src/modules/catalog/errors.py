"""catalog-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code` (guild.md §5.4's `code` field), raised from
services and turned into Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


class CategoryCycleError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "This Category cannot be its own ancestor or descendant."
    default_code = "catalog.category_cycle"


class CategoryNotFoundError(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "Category not found."
    default_code = "catalog.category_not_found"
