from datetime import date

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
    company = factory.SubFactory('crm.tests.factories.CompanyFactory')
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
    company = factory.SubFactory('crm.tests.factories.CompanyFactory')


class SubscriptionsTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.SubscriptionsType
    company = factory.SubFactory('crm.tests.factories.CompanyFactory')

    name = factory.Faker('pystr', min_chars=10, max_chars=15)
    price = factory.Faker('pyfloat', left_digits=3)
    duration_type = factory.Faker(
        'random_element',
        elements=tuple(x[0] for x in models.granularity)
    )
    duration = factory.Faker('random_int', max=60)
    rounding = factory.Faker('pybool')
    visit_limit = factory.Faker('random_int', max=30)


class EventClassFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.EventClass

    class Params:
        days = [0, 1, 2, 3, 4, 5, 6]

    company = factory.SubFactory('crm.tests.factories.CompanyFactory')
    name = factory.Faker('pystr', min_chars=10, max_chars=15)
    location = factory.SubFactory(
        'crm.tests.factories.LocationFactory',
        company=factory.SelfAttribute('..company')
    )
    coach = factory.SubFactory(
        'crm.tests.factories.CoachFactory',
        user__company=factory.SelfAttribute('...company')
    )
    date_from = factory.LazyFunction(date.today)
    date_to = None

    days_of_week__days = factory.SelfAttribute('..days')

    @factory.post_generation
    def days_of_week(self, create, extracted, **kwarg):
        if not create:
            return

        for day in kwarg['days']:
            models.DayOfTheWeekClass.objects.create(
                company=self.company,
                event=self,
                day=day
            )
