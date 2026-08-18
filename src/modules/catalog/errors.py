"""catalog-module business errors — DRF `APIException` subclasses with a
stable, dotted `default_code` (guild.md §5.4's `code` field), raised from
services and turned into Problem Details by common/api/exceptions.py.
"""

from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT


class CategoryCycleError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "This Category cannot be its own ancestor or descendant."
    default_code = "catalog.category_cycle"


class CategoryNotFoundError(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "Category not found."
    default_code = "catalog.category_not_found"


class ProductNotFoundError(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "Product not found."
    default_code = "catalog.product_not_found"


class PrimaryCategoryNotInCategoriesError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "A Product's primary Category must be one of its assigned Categories."
    default_code = "catalog.primary_category_not_in_categories"


class DuplicateAttributeError(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = "Only one value per Attribute is allowed on a Variant."
    default_code = "catalog.duplicate_attribute"


class DuplicateAttributeCombinationError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = "Another Variant of this Product already has this Attribute combination."
    default_code = "catalog.duplicate_attribute_combination"


class HardDeleteNotAllowedError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = (
        "This record can never be hard-deleted, even if no Order references it yet. "
        "Archive it instead."
    )
    default_code = "catalog.hard_delete_not_allowed"


class IncompleteDefaultLocaleContentError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = "The Product is missing required content in the default locale."
    default_code = "catalog.incomplete_default_locale_content"


class NoSellableVariantError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = "The Product must have at least one non-archived Variant to publish."
    default_code = "catalog.no_sellable_variant"


class NoReadyMediaError(APIException):
    status_code = HTTP_409_CONFLICT
    default_detail = "The Product must have at least one ready media asset to publish."
    default_code = "catalog.no_ready_media"
