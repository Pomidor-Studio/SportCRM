import datetime
from datetime import date

import factory
from django_multitenant.utils import set_current_tenant
from factory import post_generation

from crm import models
from crm.enums import GRANULARITY


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
        elements=tuple(GRANULARITY.values.keys())
    )
    duration = factory.Faker('random_int', max=60)
    rounding = factory.Faker('pybool')
    visit_limit = factory.Faker('random_int', max=30)

    event_class__events = factory.SubFactory(
        'crm.tests.factories.EventClassFactory',
        company=factory.SelfAttribute('...company')
    )

    @factory.post_generation
    def event_class(self, create, extracted, **kwargs):
        if not create:
            return

        if isinstance(kwargs['events'], models.EventClass):
            self.event_class.add(kwargs['events'])
        else:
            for event_class in kwargs['events']:
                self.event_class.add(event_class)


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


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Event

    company = factory.SubFactory('crm.tests.factories.CompanyFactory')
    event_class = factory.SubFactory(
        'crm.tests.factories.EventClassFactory',
        company=factory.SelfAttribute('..company')
    )
    canceled_at = None
    canceled_with_extending = False

    @factory.lazy_attribute
    def date(self):
        return list(self.event_class.get_calendar(
            self.event_class.date_from,
            self.event_class.date_from + datetime.timedelta(days=1)
        ).keys())[0]


class ClientFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Client

    company = factory.SubFactory('crm.tests.factories.CompanyFactory')
    name = factory.Faker('name', locale='ru')
    address = factory.Faker('address', locale='ru')
    birthday = factory.Faker(
        'date_between', start_date='-30y', end_date='-20y')
    phone_number = factory.Faker('phone_number', locale='ru')
    email_address = factory.Faker('email')
    vk_user_id = None
    balance = 0


class ClientSubscriptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ClientSubscriptions

    company = factory.SubFactory('crm.tests.factories.CompanyFactory')
    client = factory.SubFactory(
        'crm.tests.factories.ClientFactory',
        company=factory.SelfAttribute('..company')
    )
    subscription = factory.SubFactory(
        'crm.tests.factories.SubscriptionsTypeFactory',
        company=factory.SelfAttribute('..company')
    )
    purchase_date = factory.Faker(
        'date_time_between', start_date='-30d', end_date='-10d')
    start_date = factory.SelfAttribute('purchase_date')
    end_date = factory.Faker('future_datetime')
    price = factory.Faker('pyfloat', left_digits=3)
    visits_left = factory.Faker('random_int', min=1, max=30)


class ExtensionHistoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ExtensionHistory

    company = factory.SubFactory('crm.tests.factories.CompanyFactory')
    client_subscription = factory.SubFactory(
        'crm.tests.factories.ClientSubscriptionFactory',
        company=factory.SelfAttribute('..company')
    )
    reason = factory.Faker('pystr', min_chars=10, max_chars=20)
    added_visits = 1
