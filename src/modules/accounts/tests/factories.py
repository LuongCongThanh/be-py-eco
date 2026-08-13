import factory
from django.contrib.auth.hashers import make_password

from modules.accounts.models import Customer, Staff


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    email = factory.Sequence(lambda n: f"customer{n}@example.com")


class StaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Staff

    email = factory.Sequence(lambda n: f"staff{n}@example.com")
    password_hash = factory.LazyFunction(lambda: make_password("a-strong-password-123"))
    role = Staff.Role.MASTER_ADMIN
