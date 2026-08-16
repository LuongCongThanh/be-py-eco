from typing import cast

import pytest
from django.db import IntegrityError
from django.utils import timezone

from modules.accounts.models import Customer, LoginMethod
from modules.accounts.tests.factories import CustomerFactory


@pytest.mark.django_db
def test_customer_is_email_verified_reflects_verified_at() -> None:
    customer = cast(Customer, CustomerFactory())
    assert customer.is_email_verified is False

    customer.email_verified_at = timezone.now()

    assert customer.is_email_verified is True


@pytest.mark.django_db
def test_login_method_provider_is_unique_per_customer() -> None:
    customer = cast(Customer, CustomerFactory())
    LoginMethod.objects.create(
        customer=customer, provider=LoginMethod.Provider.PASSWORD, password_hash="x"
    )

    with pytest.raises(IntegrityError):
        LoginMethod.objects.create(
            customer=customer, provider=LoginMethod.Provider.PASSWORD, password_hash="y"
        )
