import datetime

import pytest
from hamcrest import assert_that, contains_inanyorder

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
