"""Query-param validation for the Storefront search endpoints.

Split in two on purpose. The serializer tests pin coercion and rejection
and need no infrastructure at all. The API tests patch `execute_search`,
because the point being proved is that invalid input is refused *before*
anything reaches the cluster — a test that needed a live OpenSearch to
demonstrate that would be testing the wrong thing.
"""

from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from django.http import QueryDict
from rest_framework import status
from rest_framework.test import APIClient

from modules.search.api.storefront.serializers import (
    AutocompleteQuerySerializer,
    SearchQuerySerializer,
)

SEARCH_URL = "/api/v1/storefront/search/products/search"
AUTOCOMPLETE_URL = "/api/v1/storefront/search/products/autocomplete"
EXECUTE_SEARCH = "modules.search.api.storefront.views.execute_search"


def _validate(query_string: str) -> SearchQuerySerializer:
    serializer = SearchQuerySerializer(data=QueryDict(query_string))
    serializer.is_valid()
    return serializer


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# --- coercion the hand-rolled parser got wrong -------------------------


def test_available_only_accepts_1_not_just_the_string_true() -> None:
    """The old parser compared against the literal "true", so `1` — which
    the declared BooleanField has always accepted — silently meant false."""
    assert _validate("available_only=1").validated_data["available_only"] is True
    assert _validate("available_only=true").validated_data["available_only"] is True
    assert _validate("available_only=false").validated_data["available_only"] is False


def test_available_only_defaults_to_false_when_absent() -> None:
    assert _validate("").validated_data["available_only"] is False


def test_repeated_attribute_value_id_becomes_a_list_of_uuids() -> None:
    first, second = uuid4(), uuid4()

    validated = _validate(f"attribute_value_id={first}&attribute_value_id={second}").validated_data

    assert validated["attribute_value_id"] == [first, second]
    assert all(isinstance(value, UUID) for value in validated["attribute_value_id"])


def test_sort_defaults_to_relevance() -> None:
    assert _validate("").validated_data["sort"] == "relevance"


def test_blank_q_is_treated_as_omitted_not_as_an_error() -> None:
    """`?q=` keeps meaning "match everything" — an empty search box must
    not be a 400."""
    serializer = _validate("q=")

    assert serializer.is_valid() is True
    assert "q" not in serializer.validated_data


# --- input the hand-rolled parser let through --------------------------


@pytest.mark.parametrize(
    ("query_string", "field"),
    [
        ("price_min=abc", "price_min"),
        ("price_max=abc", "price_max"),
        ("price_min=-5", "price_min"),
        ("sort=cheapest", "sort"),
        ("category_id=not-a-uuid", "category_id"),
        ("brand_id=not-a-uuid", "brand_id"),
        ("attribute_value_id=not-a-uuid", "attribute_value_id"),
    ],
)
def test_invalid_input_is_rejected(query_string: str, field: str) -> None:
    serializer = _validate(query_string)

    assert serializer.is_valid() is False
    assert field in serializer.errors


def test_autocomplete_requires_a_prefix() -> None:
    serializer = AutocompleteQuerySerializer(data=QueryDict(""))

    assert serializer.is_valid() is False
    assert "q" in serializer.errors


# --- the contract at the HTTP boundary ---------------------------------


@pytest.mark.django_db
def test_malformed_price_is_a_400_problem_detail_not_a_500(api_client: APIClient) -> None:
    """Previously this escaped as a ValueError, which the Problem Details
    handler passes over (it only handles APIException), so Django's own
    500 page took over."""
    with patch(EXECUTE_SEARCH) as execute:
        response = api_client.get(SEARCH_URL, {"price_min": "abc"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "invalid"
    execute.assert_not_called()


@pytest.mark.django_db
def test_unknown_sort_is_rejected_instead_of_silently_falling_back(api_client: APIClient) -> None:
    with patch(EXECUTE_SEARCH) as execute:
        response = api_client.get(SEARCH_URL, {"sort": "cheapest"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    execute.assert_not_called()


@pytest.mark.django_db
def test_autocomplete_without_a_prefix_is_a_400(api_client: APIClient) -> None:
    with patch(EXECUTE_SEARCH) as execute:
        response = api_client.get(AUTOCOMPLETE_URL)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    execute.assert_not_called()


@pytest.mark.django_db
def test_valid_input_reaches_the_cluster_with_coerced_values(
    api_client: APIClient, supported_country
) -> None:
    value_id = uuid4()

    with patch(EXECUTE_SEARCH, return_value=[]) as execute:
        response = api_client.get(
            SEARCH_URL,
            {
                "q": "áo",
                "available_only": "1",
                "attribute_value_id": str(value_id),
                "sort": "rating",
            },
        )

    assert response.status_code == status.HTTP_200_OK
    body = execute.call_args.kwargs["body"]
    assert body["sort"] == [{"rating": "desc"}]
    assert {"term": {"is_available": True}} in body["query"]["bool"]["filter"]
    assert {"term": {"attribute_value_ids": str(value_id)}} in body["query"]["bool"]["filter"]


@pytest.mark.django_db
def test_unsupported_currency_is_refused_outside_the_serializer(
    api_client: APIClient,
    supported_country,
) -> None:
    """The serializer describes `currency` but does not police it. Which
    currencies exist is decided further in: `localization` checks the
    Supported Country allows it, then `pricing` checks it can be converted
    (ADR-0008). EUR fails the first of those."""
    with patch(EXECUTE_SEARCH) as execute:
        response = api_client.get(SEARCH_URL, {"currency": "EUR"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "localization.unsupported_currency"
    execute.assert_not_called()
