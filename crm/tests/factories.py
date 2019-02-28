import factory
from django_multitenant.utils import set_current_tenant
from factory import post_generation

from .. import models


class CompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Company

    display_name = factory.Faker('pystr', min_chars=10, max_chars=30)

    @post_generation
    def set_tenant(self, create, extracted, **kwargs):
        if not create:
            return

        set_current_tenant(self)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Faker('pystr', min_chars=20, max_chars=30)
    first_name = factory.Faker('first_name', locale='ru')
    last_name = factory.Faker('last_name', locale='ru')
    email = factory.Faker('email')
    company = factory.SubFactory(CompanyFactory)
    password = factory.PostGenerationMethodCall(
        'set_password', 'defaultpassword')


class CoachFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Coach

    user = factory.SubFactory(UserFactory)
    company = factory.SelfAttribute('user.company')


class ManagerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Manager

    user = factory.SubFactory(UserFactory)
    company = factory.SelfAttribute('user.company')


class LocationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Location

    name = factory.Faker('company', locale='ru')
    address = factory.Faker('address', locale='ru')
    company = factory.SubFactory(CompanyFactory)


class SubscriptionsTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.SubscriptionsType
    company = factory.SubFactory(CompanyFactory)

    name = factory.Faker('pystr', min_chars=10, max_chars=15)
    price = factory.Faker('pyfloat', left_digits=3)
    duration_type = factory.Faker(
        'random_element',
        elements=tuple(x[0] for x in models.granularity)
    )
    duration = factory.Faker('random_int', max=60)
    rounding = factory.Faker('pybool')
    visit_limit = factory.Faker('random_int', max=30)
