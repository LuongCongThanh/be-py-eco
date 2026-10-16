"""Request and response shapes for the Storefront search endpoints.

`SearchQuerySerializer` and `AutocompleteQuerySerializer` are load-bearing:
the views validate through them rather than re-parsing `query_params` by
hand, so one declaration serves the OpenAPI schema, validation and
coercion at once. Before this, the views parsed by hand and a malformed
`price_min` escaped as a `ValueError` — an unhandled 500, outside the
Problem Details contract every other endpoint honours.

The response serializers describe what the endpoints actually return and
do not shape it: search returns the index document as stored, plus a
converted price. Narrowing that to a whitelist would change the response
contract, which is a separate decision from validating input.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from common.api.pagination import CursorPageSerializer
from modules.search.selectors.search_query import SORT_CLAUSES


@extend_schema_field(serializers.CharField)
class AttributeFilterField(serializers.Field):
    """One `<attribute>:<value>` facet selection, split at the boundary.

    Subclasses `Field` rather than `CharField` because it does not return a
    string: it returns the parsed pair, and narrowing a supertype's return
    type would be a lie the type checker rightly rejects.

    Validated here rather than deeper in so a malformed selection is a 400
    naming the parameter, instead of a meaningless token reaching OpenSearch
    and coming back as zero results -- the very symptom this facet work
    exists to fix.
    """

    def to_internal_value(self, data: object) -> tuple[str, str]:
        attribute, separator, value = str(data).partition(":")
        if not separator or not attribute or not value or ":" in value:
            raise serializers.ValidationError(
                'Expected "<attribute>:<value>", for example "color:red".'
            )
        return attribute, value

    def to_representation(self, value: tuple[str, str]) -> str:
        return ":".join(value)


class SearchQuerySerializer(CursorPageSerializer):
    """Validated query params for Product search.

    `currency` is described here but deliberately not constrained: which
    currencies exist is `pricing`'s to decide (ADR-0008), and repeating
    the list here would drift the first time one is added.
    """

    q = serializers.CharField(
        required=False,
        help_text="Free-text query. Omitted or blank matches every published Product.",
    )
    category_id = serializers.UUIDField(required=False)
    brand_id = serializers.UUIDField(required=False)
    attribute = serializers.ListField(
        child=AttributeFilterField(),
        required=False,
        help_text='Repeatable, as "<attribute>:<value>" (e.g. color:red). Values of '
        "the same Attribute are OR-ed together; different Attributes are AND-ed.",
    )
    price_min = serializers.IntegerField(required=False, min_value=0)
    price_max = serializers.IntegerField(required=False, min_value=0)
    available_only = serializers.BooleanField(required=False, default=False)
    # Derived from SORT_CLAUSES rather than restated: the module that
    # knows how to sort is the one that should say what sorts exist.
    sort = serializers.ChoiceField(choices=list(SORT_CLAUSES), required=False, default="relevance")
    currency = serializers.CharField(
        required=False,
        help_text="Transaction Currency for the returned prices; defaults to VND.",
    )


class AutocompleteQuerySerializer(serializers.Serializer):
    """`q` is required: a prefix-match with no prefix is not a question
    worth answering, and returning every Product to a suggestion box is
    worse than refusing.

    Deliberately not paginated. Suggestions are inherently top-N -- nobody
    pages through an autocomplete dropdown -- and the size is fixed by the
    server rather than accepted from the client, which is what stops this
    endpoint being used as an unmetered search.
    """

    q = serializers.CharField(help_text="Prefix to match against Product names.")


@extend_schema_serializer(component_name="SearchConvertedPrice")
class ConvertedPriceSerializer(serializers.Serializer):
    """Response shape only — used for OpenAPI docs, not for validation.

    Deliberately a local copy rather than an import of catalog's identical
    serializer: a module's response shape is its own, and reaching into
    another module's API layer for one would be a dependency pointing the
    wrong way (ADR-0003).

    The explicit `component_name` is the price of that independence — two
    modules describing the same shape would otherwise collide on one
    OpenAPI component name. Catalog's keeps the unprefixed name because it
    was there first. A third module needing this shape would be the signal
    to promote it to a shared one rather than rename again.
    """

    amount = serializers.IntegerField(
        allow_null=True,
        help_text="Integer minor-unit amount in `currency`; null if no rate has been "
        "synced for this pair (see is_stale).",
    )
    currency = serializers.CharField()
    is_stale = serializers.BooleanField(
        help_text="True if the required Exchange Rate is missing or expired."
    )


class ProductDocumentSerializer(serializers.Serializer):
    """Response shape only — the indexed document as `build_product_document`
    stores it. Returned as-is by autocomplete."""

    product_id = serializers.UUIDField()
    sku = serializers.ListField(child=serializers.CharField())
    barcode = serializers.ListField(child=serializers.CharField())
    name = serializers.CharField(allow_blank=True)
    category_ids = serializers.ListField(child=serializers.UUIDField())
    brand_id = serializers.UUIDField(allow_null=True)
    attribute_value_ids = serializers.ListField(child=serializers.UUIDField())
    base_price_vnd = serializers.IntegerField(allow_null=True)
    is_available = serializers.BooleanField()
    popularity = serializers.IntegerField()
    rating = serializers.FloatField()
    published_at = serializers.DateTimeField()


class SearchResultSerializer(ProductDocumentSerializer):
    """Response shape only — the same document, plus the price derived from
    its still-VND `base_price_vnd` at read time."""

    price = ConvertedPriceSerializer()
