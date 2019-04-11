from datetime import date, timedelta
from typing import List

import pytest
from hamcrest import assert_that, is_, has_length, contains

from crm import models
from crm.enums import GRANULARITY
from crm.events import range_days
from crm.models import SubscriptionsTypeEventFilter

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('granularity', [
    GRANULARITY.DAY, GRANULARITY.WEEK, GRANULARITY.MONTH, GRANULARITY.YEAR
])
def test_start_date_non_rounded(
    granularity,
    subscriptions_type_factory
):
    st = subscriptions_type_factory(
        duration_type=granularity,
        duration=1,
        rounding=False
    )
    start_date = date(2019, 2, 28)
    assert_that(st.start_date(start_date), is_(start_date))


@pytest.mark.parametrize('granularity, start, expected', [
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 2, 28)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 2, 25)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 2, 1)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2019, 1, 1))
])
def test_start_date_rounded(
    granularity,
    start,
    expected,
    subscriptions_type_factory
):
    st = subscriptions_type_factory(
        duration_type=granularity,
        duration=1,
        rounding=True
    )
    assert_that(st.start_date(start), is_(expected))


@pytest.mark.parametrize('granularity, start, expected', [
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 2, 28)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 3, 6)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 3, 27)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2020, 2, 27))
])
def test_end_date_non_rounded(
    granularity,
    start,
    expected,
    subscriptions_type_factory
):
    st = subscriptions_type_factory(
        duration_type=granularity,
        duration=1,
        rounding=False
    )
    assert_that(st.end_date(start), is_(expected))


@pytest.mark.parametrize('granularity, start, expected', [
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 2, 28)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 3, 3)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 2, 28)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2019, 12, 31))
])
def test_end_date_rounded(
    granularity,
    start,
    expected,
    subscriptions_type_factory
):
    st = subscriptions_type_factory(
        duration_type=granularity,
        duration=1,
        rounding=True
    )
    assert_that(st.end_date(start), is_(expected))


def test_events_to_date_active(
    event_class_factory,
    company_factory,
    subscriptions_type_factory,
):
    start_date = date(2019, 1, 1)
    end_date = date(2019, 1, 31)
    company = company_factory()

    # By default event class if for every day
    ecs: List[models.EventClass] = event_class_factory.create_batch(
        2,
        company=company,
        date_from=start_date,
        date_to=end_date
    )

    cs: models.SubscriptionsType = subscriptions_type_factory(
        company=company,
        event_class__events=ecs,
        rounding=True,
        duration=1,
        duration_type=GRANULARITY.MONTH
    )

    cs_events = cs.events_to_date(
        from_date=start_date, to_date=start_date + timedelta(days=6))

    # Client subscription have 2 event classes, so one week count * 2

    assert_that(cs_events, has_length(14))
    for idx, day in enumerate(
            range_days(start_date, start_date + timedelta(days=7))):
        check_idx = idx * 2
        assert_that(cs_events[check_idx].date, is_(day))
        assert_that(cs_events[check_idx + 1].date, is_(day))


def test_events_to_date_active_with_some_canceled(
    event_class_factory,
    event_factory,
    company_factory,
    subscriptions_type_factory,
):
    start_date = date(2019, 1, 1)
    end_date = date(2019, 1, 31)
    company = company_factory()

    # By default event class if for every day
    ecs: List[models.EventClass] = event_class_factory.create_batch(
        2,
        company=company,
        date_from=start_date,
        date_to=end_date
    )

    cs: models.SubscriptionsType = subscriptions_type_factory(
        company=company,
        event_class__events=ecs,
        rounding=True,
        duration=1,
        duration_type=GRANULARITY.MONTH
    )
    event_factory(
        company=company,
        event_class=ecs[0],
        date=date(2019, 1, 1),
        canceled_at=date(2019, 1, 1)
    )
    event_factory(
        company=company,
        event_class=ecs[1],
        date=date(2019, 1, 2),
        canceled_at=date(2019, 1, 1)
    )

    cs_events = cs.events_to_date(
        from_date=start_date, to_date=start_date + timedelta(days=6))

    # Client subscription have 2 event classes, so one week count * 2 minus
    # 2 canceled events

    assert_that(cs_events, has_length(12))


def test_events_to_date_canceled(
    event_class_factory,
    event_factory,
    company_factory,
    subscriptions_type_factory,
):
    start_date = date(2019, 1, 1)
    end_date = date(2019, 1, 31)
    company = company_factory()

    # By default event class if for every day
    ecs: List[models.EventClass] = event_class_factory.create_batch(
        2,
        company=company,
        date_from=start_date,
        date_to=end_date
    )

    cs: models.SubscriptionsType = subscriptions_type_factory(
        company=company,
        event_class__events=ecs,
        rounding=True,
        duration=1,
        duration_type=GRANULARITY.MONTH
    )
    canceled_event_1 = event_factory(
        company=company,
        event_class=ecs[0],
        date=date(2019, 1, 1),
        canceled_at=date(2019, 1, 1)
    )
    canceled_event_2 = event_factory(
        company=company,
        event_class=ecs[1],
        date=date(2019, 1, 2),
        canceled_at=date(2019, 1, 1)
    )

    cs_events = cs.events_to_date(
        from_date=start_date,
        to_date=start_date + timedelta(days=6),
        filter_runner=SubscriptionsTypeEventFilter.CANCELED
    )

    # Client subscription have 2 event classes, so one week count * 2

    assert_that(cs_events, has_length(2))
    assert_that(cs_events, contains(
        canceled_event_1,
        canceled_event_2
    ))


def test_events_to_date_all(
    event_class_factory,
    event_factory,
    company_factory,
    subscriptions_type_factory,
):
    start_date = date(2019, 1, 1)
    end_date = date(2019, 1, 31)
    company = company_factory()

    # By default event class if for every day
    ecs: List[models.EventClass] = event_class_factory.create_batch(
        2,
        company=company,
        date_from=start_date,
        date_to=end_date
    )

    cs: models.SubscriptionsType = subscriptions_type_factory(
        company=company,
        event_class__events=ecs,
        rounding=True,
        duration=1,
        duration_type=GRANULARITY.MONTH
    )
    event_factory(
        company=company,
        event_class=ecs[0],
        date=date(2019, 1, 1),
        canceled_at=date(2019, 1, 1)
    )
    event_factory(
        company=company,
        event_class=ecs[1],
        date=date(2019, 1, 2),
        canceled_at=date(2019, 1, 1)
    )

    cs_events = cs.events_to_date(
        from_date=start_date,
        to_date=start_date + timedelta(days=6),
        filter_runner=SubscriptionsTypeEventFilter.ALL
    )

    # Client subscription have 2 event classes, so one week count * 2 and
    # 2 canceled events

    assert_that(cs_events, has_length(14))
