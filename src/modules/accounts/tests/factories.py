from typing import Any, cast

import factory
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from modules.accounts.models import Customer, Staff, StaffTOTPDevice


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    email = factory.Sequence(lambda n: f"customer{n}@example.com")
    # Declared with the model's own defaults so tests can override them --
    # Storefront reads resolve against these (localization's
    # resolve_storefront_context).
    preferred_locale = ""
    preferred_currency = ""


class StaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Staff
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"staff{n}@example.com")
    password_hash = factory.LazyFunction(lambda: make_password("a-strong-password-123"))
    role = Staff.Role.MASTER_ADMIN

    @factory.post_generation
    def mfa_confirmed(obj: Any, create: bool, extracted: bool, **kwargs: Any) -> None:
        """Pass `mfa_confirmed=True` to get a confirmed TOTP device — most
        service-level tests act as an already-MFA'd Staff; the MFA
        setup/confirm flow itself is tested separately without this."""
        if not create or not extracted:
            return
        device = StaffTOTPDevice.objects.create(staff=cast(Staff, obj))
        device.confirmed_at = timezone.now()
        device.save(update_fields=["confirmed_at"])
