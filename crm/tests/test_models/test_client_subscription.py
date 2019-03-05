from datetime import date, timedelta
from typing import List

import pytest
from hamcrest import (
    assert_that, contains_inanyorder, has_properties, is_,
    has_length,
)
from pytest_mock import MockFixture

from crm import models
from crm.enums import GRANULARITY
from crm.events import range_days

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('days, expected_delta', [
    ([0, 1, 2, 3, 4, 5, 6], 1),
    ([0], 7),
    ([1, 4], 1),
    ([0, 4], 4)
])
def test_nearest_extended_end_date(
    days,
    expected_delta,
    company_factory,
    event_class_factory,
    client_subscription_factory
):
    start_date = date(2019, 2, 25)
    company = company_factory()
    ecs: List[models.EventClass] = event_class_factory.create_batch(
        2, company=company, date_from=start_date, days=days)
    cs: models.ClientSubscriptions = client_subscription_factory(
        company=company,
        subscription__event_class__events=ecs,
        subscription__rounding=False,
        subscription__duration=7,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date,
    )

    assert_that(
        cs.nearest_extended_end_date(),
        is_(cs.end_date + timedelta(days=expected_delta))
    )


def test_nearest_extended_end_date_without_events(
    company_factory,
    client_subscription_factory
):
    company = company_factory()
    # Client subscription don't have any event class attached
    cs: models.ClientSubscriptions = client_subscription_factory(
        company=company,
        subscription__event_class__events=[]
    )

    assert_that(
        cs.nearest_extended_end_date(),
        is_(cs.end_date)
    )


def test_nearest_extended_end_date_for_ended_events(
    company_factory,
    event_class_factory,
    client_subscription_factory
):
    start_date = date.today()
    end_date = date.today() + timedelta(days=7)
    company = company_factory()
    ecs: List[models.EventClass] = event_class_factory.create_batch(
        2,
        company=company,
        date_from=start_date,
        date_to=end_date
    )

    # Client subscription ends after every event class ends
    cs: models.ClientSubscriptions = client_subscription_factory(
        company=company,
        subscription__event_class__events=ecs,
        subscription__rounding=False,
        subscription__duration=10,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )

    assert_that(
        cs.nearest_extended_end_date(),
        is_(cs.end_date)
    )


def test_nearest_extended_end_date_for_no_future_events(
    company_factory,
    event_class_factory,
    client_subscription_factory
):
    start_date = date(2019, 2, 25)

    company = company_factory()
    ecs1 = event_class_factory(
        company=company,
        date_from=start_date,
        date_to=start_date + timedelta(days=13),
        days=[0]
    )
    ecs2 = event_class_factory(
        company=company,
        date_from=start_date,
        date_to=start_date + timedelta(days=14),
        days=[0]
    )

    # Client subscription ends after every event class ends
    # Because there is only event at monday, and clients
    # subscriptions ends at tuesday
    cs: models.ClientSubscriptions = client_subscription_factory(
        company=company,
        subscription__event_class__events=[ecs1, ecs2],
        subscription__rounding=False,
        subscription__duration=10,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )

    assert_that(
        cs.nearest_extended_end_date(),
        is_(cs.end_date)
    )


def test_extend_duration_with_new_end_date(
    client_subscription_factory,
    mocker: MockFixture
):
    start_date = date(2019, 2, 25)
    new_end_date = start_date + timedelta(days=14)

    mocker.patch(
        'crm.models.ClientSubscriptions.nearest_extended_end_date',
        return_value=new_end_date
    )

    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__event_class__events=[],
        subscription__rounding=False,
        subscription__duration=7,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )
    old_visits = cs.visits_left

    spy = mocker.spy(models.ExtensionHistory.objects, 'create')

    cs.extend_duration(10, reason='TEST')

    cs.refresh_from_db()

    assert_that(cs, has_properties(
        visits_left=old_visits + 10,
        end_date=new_end_date
    ))
    spy.assert_called_once_with(
        client_subscription=cs,
        reason='TEST',
        added_visits=10,
        extended_to=new_end_date
    )


def test_extend_duration_without_new_end_date(
    client_subscription_factory,
    mocker: MockFixture
):
    start_date = date(2019, 2, 25)
    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__event_class__events=[],
        subscription__rounding=False,
        subscription__duration=7,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )
    old_end_date = cs.end_date

    mocker.patch(
        'crm.models.ClientSubscriptions.nearest_extended_end_date',
        return_value=cs.end_date
    )

    old_visits = cs.visits_left

    spy = mocker.spy(models.ExtensionHistory.objects, 'create')

    cs.extend_duration(10, reason='TEST')

    cs.refresh_from_db()

    assert_that(cs, has_properties(
        visits_left=old_visits + 10,
        end_date=old_end_date
    ))
    spy.assert_called_once_with(
        client_subscription=cs,
        reason='TEST',
        added_visits=10,
        extended_to=None
    )


def test_extend_duration_without_new_end_date_and_zero(
    client_subscription_factory,
    mocker: MockFixture
):
    start_date = date(2019, 2, 25)
    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__event_class__events=[],
        subscription__rounding=False,
        subscription__duration=7,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )
    old_end_date = cs.end_date

    mocker.patch(
        'crm.models.ClientSubscriptions.nearest_extended_end_date',
        return_value=cs.end_date
    )

    old_visits = cs.visits_left

    spy = mocker.spy(models.ExtensionHistory.objects, 'create')

    cs.extend_duration(0, reason='TEST')

    cs.refresh_from_db()

    assert_that(cs, has_properties(
        visits_left=old_visits,
        end_date=old_end_date
    ))
    spy.assert_not_called()


def test_extend_by_cancellation_no_future_date(
    client_subscription_factory,
    event_factory,
    mocker: MockFixture
):
    start_date = date(2019, 2, 25)
    event = event_factory(
        event_class__date_from=start_date,
        canceled_at=date(2019, 2, 26)
    )
    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__event_class__events=event.event_class,
        subscription__rounding=False,
        subscription__duration=7,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )
    old_end_date = cs.end_date

    mocker.patch(
        'crm.models.ClientSubscriptions.nearest_extended_end_date',
        return_value=cs.end_date
    )

    spy = mocker.spy(models.ExtensionHistory.objects, 'create')

    cs.extend_by_cancellation(event)

    cs.refresh_from_db()

    assert_that(cs, has_properties(
        end_date=old_end_date
    ))
    spy.assert_not_called()


def test_extend_by_cancellation_with_future_date(
    client_subscription_factory,
    event_factory,
    mocker: MockFixture
):
    start_date = date(2019, 2, 25)
    event = event_factory(
        event_class__date_from=start_date,
        canceled_at=date(2019, 2, 26)
    )
    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__event_class__events=event.event_class,
        subscription__rounding=False,
        subscription__duration=7,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start_date
    )
    new_end_date = date(2019, 2, 27)

    mocker.patch(
        'crm.models.ClientSubscriptions.nearest_extended_end_date',
        return_value=new_end_date
    )

    spy = mocker.spy(models.ExtensionHistory.objects, 'create')

    cs.extend_by_cancellation(event)

    cs.refresh_from_db()

    assert_that(cs, has_properties(
        end_date=new_end_date
    ))
    spy.assert_called_once_with(
        client_subscription=cs,
        reason=f'В связи с отменой тренировки {event}',
        added_visits=0,
        related_event=event,
        extended_to=new_end_date
    )


def test_qs_active_subscriptions(
    subscriptions_type_factory,
    client_subscription_factory,
    event_factory
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1)
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.MONTH,
        rounding=False,
        event_class__events=event.event_class
    )

    active_subs = client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 25),
        start_date=date(2019, 2, 25)
    )
    # outdated_sub
    client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 1, 1),
        start_date=date(2019, 1, 1)
    )
    # future_sub
    client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 3, 1),
        start_date=date(2019, 3, 1)
    )
    # empty_sub
    client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 25),
        start_date=date(2019, 2, 25),
        visits_left=0
    )

    assert_that(
        models.ClientSubscriptions
        .objects
        .get_queryset()
        .active_subscriptions(event),

        contains_inanyorder(*active_subs)
    )


def test_manager_active_subscriptions(
    mocker: MockFixture
):
    mock = mocker.patch(
        'crm.models.ClientSubscriptionQuerySet.active_subscriptions')

    models.ClientSubscriptions.objects.active_subscriptions(mocker.ANY)

    mock.assert_called_once_with(mocker.ANY)


def test_manager_extend_by_cancellation(
    subscriptions_type_factory,
    client_subscription_factory,
    event_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1)
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.MONTH,
        rounding=False,
        event_class__events=event.event_class
    )

    client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 25),
        start_date=date(2019, 2, 25)
    )

    mock = mocker.patch(
        'crm.models.ClientSubscriptions.extend_by_cancellation')

    models.ClientSubscriptions.objects.extend_by_cancellation(event)

    assert_that(mock.call_count, is_(3))
    mock.assert_any_call(event)


def test_events_to_date(
    event_class_factory,
    company_factory,
    client_subscription_factory,
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

    cs: models.ClientSubscriptions = client_subscription_factory(
        company=company,
        subscription__event_class__events=ecs,
        subscription__rounding=True,
        subscription__duration=1,
        subscription__duration_type=GRANULARITY.MONTH,
        start_date=start_date,
        end_date=start_date + timedelta(days=6)
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
