import datetime

import pytest
from hamcrest import assert_that, contains_inanyorder, none, is_

from crm import models
from crm.enums import GRANULARITY

pytestmark = pytest.mark.django_db


def test_manager_with_active_subscription_to_event(
    subscriptions_type_factory,
    event_factory,
    client_subscription_factory
):
    event = event_factory(
        date=datetime.date(2019, 2, 25),
        event_class__date_from=datetime.date(2019, 1, 1)
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.MONTH,
        rounding=False,
        event_class__events=event.event_class
    )

    cs = client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=datetime.date(2019, 2, 25),
        start_date=datetime.date(2019, 2, 25)
    )

    clients = models.Client.objects.with_active_subscription_to_event(event)

    assert_that(clients, contains_inanyorder(*[x.client for x in cs]))


def test_client_last_subscription_all(
    subscriptions_type_factory,
    event_factory,
    client_subscription_factory,
    client_factory
):
    event = event_factory(
        date=datetime.date(2019, 2, 25),
        event_class__date_from=datetime.date(2019, 1, 1)
    )
    subtype_deleted = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.MONTH,
        rounding=False,
        event_class__events=event.event_class,
    )
    # Manual delete as SafeDeleteModel overrides deleted field upon saving
    # created models
    subtype_deleted.delete()
    subtype = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.YEAR,
        rounding=False,
        event_class__events=event.event_class
    )
    client = client_factory(company=event.company)
    client_subscription_factory(
        client=client,
        company=event.company,
        subscription=subtype,
        purchase_date=datetime.date(2019, 2, 25),
        start_date=datetime.date(2019, 2, 25)
    )
    deleted_cs = client_subscription_factory(
        client=client,
        company=event.company,
        subscription=subtype_deleted,
        purchase_date=datetime.date(2019, 2, 26),
        start_date=datetime.date(2019, 2, 26)
    )

    assert_that(client.last_sub(with_deleted=True), is_(deleted_cs))


def test_client_last_subscription_active(
    subscriptions_type_factory,
    event_factory,
    client_subscription_factory,
    client_factory
):
    event = event_factory(
        date=datetime.date(2019, 2, 25),
        event_class__date_from=datetime.date(2019, 1, 1)
    )
    subtype_deleted = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.MONTH,
        rounding=False,
        event_class__events=event.event_class,
    )
    # Manual delete as SafeDeleteModel overrides deleted field upon saving
    # created models
    subtype_deleted.delete()
    subtype = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.YEAR,
        rounding=False,
        event_class__events=event.event_class
    )
    client = client_factory(company=event.company)
    non_deleted_cs = client_subscription_factory(
        client=client,
        company=event.company,
        subscription=subtype,
        purchase_date=datetime.date(2019, 2, 25),
        start_date=datetime.date(2019, 2, 25)
    )
    client_subscription_factory(
        client=client,
        company=event.company,
        subscription=subtype_deleted,
        purchase_date=datetime.date(2019, 2, 26),
        start_date=datetime.date(2019, 2, 26)
    )

    assert_that(client.last_sub(), is_(non_deleted_cs))


def test_client_no_last_subscription(
    client_factory
):
    client = client_factory()

    assert_that(client.last_sub(), none())
