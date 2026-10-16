"""Describe responses in OpenAPI the way they actually come out.

Every success response leaves through `success_envelope` as
`{"data": ..., "meta": {...}}`, but views declared bare serializers --
`responses=ProductStorefrontSerializer(many=True)` -- promising a plain
array of Products. No endpoint has ever returned that. The schema was
wrong the same way everywhere, which is worse than being wrong in one
place: a generated client breaks on its first call, and someone reading
the spec has no way to tell it is lying.

`envelope.py` exists precisely so no module reshapes its own responses. It
succeeded at runtime and had no counterpart on the schema side; this is
that counterpart, so the shape is stated once for both.

Deliberately called at each view rather than installed as a spectacular
postprocessing hook. A hook cannot be forgotten on the thirtieth view, but
it makes the view and its generated schema disagree textually with nothing
in the code connecting them -- action at a distance that is hard for a
reader, human or agent, to follow. Explicit here beats invisible.

Responses with no body (`{204: None}`, `{202: None}`) are not wrapped:
there is nothing to envelope, so they are outside this helper's remit
rather than a special case inside it.
"""

from __future__ import annotations

from typing import Any

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

# inline_serializer mints a new class per call, so wrapping the same
# serializer from six different views would produce six distinct classes
# sharing one component name -- which drf-spectacular rightly refuses as
# "identical names, different identities". Cache by component name so the
# same shape is always the same class.
_COMPONENTS: dict[str, Any] = {}


class RequestMetaSerializer(serializers.Serializer):
    request_id = serializers.CharField()


class PaginationMetaSerializer(serializers.Serializer):
    """The `meta.pagination` object specified in guild.md §5.3."""

    next_cursor = serializers.CharField(
        allow_null=True, help_text="Pass back as `cursor` to fetch the next page; null on the last."
    )
    has_more = serializers.BooleanField()
    page_size = serializers.IntegerField()


class PaginatedMetaSerializer(RequestMetaSerializer):
    pagination = PaginationMetaSerializer()


def enveloped(
    serializer_class: type[serializers.BaseSerializer],
    *,
    many: bool = False,
    paginated: bool = False,
) -> Any:
    """Wrap `serializer_class` in the `{data, meta}` envelope the view emits.

    Takes the class, not an instance, so every call site reads the same way
    whether or not it is a collection: `enveloped(Foo)` and
    `enveloped(Foo, many=True)`.

    `paginated=True` adds `meta.pagination`, so the schema promises it only
    where a view actually sends it.
    """
    component = f"Enveloped{serializer_class.__name__.removesuffix('Serializer')}"
    if many:
        component += "List"
    if paginated:
        component += "Page"

    if component not in _COMPONENTS:
        meta_class = PaginatedMetaSerializer if paginated else RequestMetaSerializer
        _COMPONENTS[component] = inline_serializer(
            name=component,
            fields={"data": serializer_class(many=many), "meta": meta_class()},
        )
    return _COMPONENTS[component]
