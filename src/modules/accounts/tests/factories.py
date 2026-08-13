import factory

from modules.accounts.models import Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    email = factory.Sequence(lambda n: f"customer{n}@example.com")
