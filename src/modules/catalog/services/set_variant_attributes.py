"""Attach an Attribute Value combination to a Variant — guild.md §15
Slice 2, commit 3.

The combination is encoded into `Variant.attribute_combination_key`
(sorted `AttributeValue` ids, joined) so "unique Attribute combination per
Product" is a real database constraint
(`unique_attribute_combination_per_product`), not just an application
check race-prone under concurrent writes. This service still validates
up front so callers get a clean domain error instead of a raw
`IntegrityError` in the common case.
"""

from __future__ import annotations

from django.db import transaction

from modules.catalog.errors import DuplicateAttributeCombinationError, DuplicateAttributeError
from modules.catalog.models.attribute import AttributeValue
from modules.catalog.models.variant import Variant, VariantAttributeValue


def _combination_key(attribute_values: list[AttributeValue]) -> str:
    return ":".join(sorted(str(value.id) for value in attribute_values))


@transaction.atomic
def set_variant_attributes(*, variant: Variant, attribute_values: list[AttributeValue]) -> Variant:
    attribute_ids = [value.attribute_id for value in attribute_values]
    if len(attribute_ids) != len(set(attribute_ids)):
        raise DuplicateAttributeError()

    combination_key = _combination_key(attribute_values)
    conflict_exists = (
        Variant.objects.filter(
            product_id=variant.product_id,
            attribute_combination_key=combination_key,
        )
        .exclude(pk=variant.pk)
        .exists()
    )
    if combination_key and conflict_exists:
        raise DuplicateAttributeCombinationError()

    VariantAttributeValue.objects.filter(variant=variant).delete()
    VariantAttributeValue.objects.bulk_create(
        [
            VariantAttributeValue(
                variant=variant,
                attribute_id=value.attribute_id,
                attribute_value=value,
            )
            for value in attribute_values
        ]
    )
    variant.attribute_combination_key = combination_key
    variant.save(update_fields=["attribute_combination_key", "updated_at"])
    return variant
