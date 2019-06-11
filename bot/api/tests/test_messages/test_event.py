import datetime

import pytest
from hamcrest import assert_that, is_

from bot.api.messages.event import CancelledEvent
from bot.api.messages.event_class import FutureEvent
from crm.enums import GRANULARITY


pytestmark = pytest.mark.django_db


def test_cancelled_event_message(
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

    cs = client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=datetime.date(2019, 2, 25),
        start_date=datetime.date(2019, 2, 25)
    )

    msg_sender = CancelledEvent(cs.client, event=event)

    assert_that(msg_sender.prepare_generalized_message(), is_(
        f'Была отменена тренировка на {event.date:%d.%m.%Y} по '
        f'{event.event_class}'
    ))


def test_notify_future_event_message(
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

    cs = client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=datetime.date(2019, 2, 25),
        start_date=datetime.date(2019, 2, 25)
    )

    msg_sender = FutureEvent(cs.client, event=event)

    assert_that(msg_sender.prepare_generalized_message(), is_(
        f'{event.date:%d.%m.%Y} у Вас предстоит тренировка по {event.event_class}\n'
        f'Тренер: {event.event_class.coach}'
    ))

