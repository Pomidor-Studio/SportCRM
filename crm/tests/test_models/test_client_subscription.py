from datetime import date, datetime, timedelta
from typing import List

import pytest
import pytz
from freezegun import freeze_time
from hamcrest import (
    assert_that, calling, contains_inanyorder, has_properties, is_,
    has_length, raises,
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
    old_end_date = cs.end_date

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
        extended_to=new_end_date,
        extended_from=old_end_date,
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
        extended_to=None,
        extended_from=None
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
    old_end_date = cs.end_date

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
        extended_to=new_end_date,
        extended_from=old_end_date,
    )


def test_qs_active_subscriptions_to_event(
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
        .active_subscriptions_to_event(event),

        contains_inanyorder(*active_subs)
    )


def test_manager_active_subscriptions_to_event(
    mocker: MockFixture
):
    mock = mocker.patch(
        'crm.models.ClientSubscriptionQuerySet.active_subscriptions_to_event')

    models.ClientSubscriptions.objects.active_subscriptions_to_event(mocker.ANY)

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


@pytest.mark.parametrize('visits_left, expected_len', [
    (0, 0),
    (1, 1),
    (2, 2),
    (100, 14)
])
def test_remained_events(
    visits_left,
    expected_len,
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
        end_date=start_date + timedelta(days=6),
        visits_left=visits_left
    )
    # End date is overridden by save, so set it forced
    cs.end_date = start_date + timedelta(days=6)
    cs.save()

    with freeze_time('2019-01-01'):
        remained_events = cs.remained_events()

    assert_that(remained_events, has_length(expected_len))


@pytest.mark.parametrize('visits_left, expected', [
    (0, False),
    (1, False),
    (7, False),
    (8, True),
    (100, True)
])
def test_is_overlapping(
    visits_left,
    expected,
    event_class_factory,
    company_factory,
    client_subscription_factory,
):
    start_date = date(2019, 1, 1)
    end_date = date(2019, 1, 7)
    company = company_factory()

    # By default event class if for every day
    ecs = event_class_factory(
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
        visits_left=visits_left
    )

    assert_that(cs.is_overlapping(), is_(expected))


@pytest.mark.parametrize('start,end,visits,expected', [
    (date(2019, 1, 1), date(2019, 1, 7), 1, True),
    (date(2019, 1, 5), date(2019, 1, 7), 1, False),
    (date(2019, 1, 1), date(2019, 1, 3), 1, False),
    (date(2019, 1, 1), date(2019, 1, 7), 0, False),
])
def test_is_active_at_date(
    start,
    end,
    visits,
    expected,
    client_subscription_factory
):
    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__rounding=False,
        subscription__duration=30,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=start,
        visits_left=visits
    )
    # Override cs end date
    cs.end_date = end
    cs.save()

    assert_that(cs.is_active_at_date_without_events(date(2019, 1, 4)), is_(expected))


@pytest.mark.parametrize('is_active_at_date,events_to_date,visits,expected', [
    (False, ['event1'], 1, False),
    (True, ['event1'], 2, True),
    (True, ['event1'], 1, False),
    (True, ['event1', 'event2'], 1, False)
])
def test_is_active_to_date(
    is_active_at_date,
    events_to_date,
    visits,
    expected,
    client_subscription_factory,
    mocker: MockFixture
):
    cs: models.ClientSubscriptions = client_subscription_factory(
        subscription__rounding=False,
        subscription__duration=30,
        subscription__duration_type=GRANULARITY.DAY,
        start_date=date(2019, 1, 1),
        visits_left=visits
    )
    mocker.patch.object(
        cs, 'is_active_at_date_without_events', return_value=is_active_at_date)
    mocker.patch.object(
        cs.subscription, 'events_to_date', return_value=events_to_date)

    assert_that(cs.is_active_to_date(date(2019, 1, 1)), is_(expected))


def test_manager_revoke_extending(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event.event_class
    )
    cs_list = client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    for cs in cs_list:
        extension_history_factory(
            company=event.company,
            client_subscription=cs,
            added_visits=0,
            date_extended=datetime(2019, 2, 25, tzinfo=pytz.utc),
            extended_from=date(2019, 2, 25),
            extended_to=date(2019, 2, 26),
            related_event=event
        )

    mock = mocker.patch('crm.models.ClientSubscriptions.revoke_extending')

    with freeze_time(date(2019, 2, 25)):
        models.ClientSubscriptions.objects.revoke_extending(event)

    assert_that(mock.call_count, is_(3))


def test_manager_revoke_extending_with_empty_extension_history(
    subscriptions_type_factory,
    event_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.MONTH,
        rounding=False,
        event_class__events=event.event_class
    )

    mock = mocker.patch('crm.models.ClientSubscriptions.revoke_extending')

    with freeze_time(date(2019, 2, 24)):
        models.ClientSubscriptions.objects.revoke_extending(event)

    mock.assert_not_called()


def test_manager_revoke_extending_on_non_active_event(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event.event_class
    )
    cs_list = client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    for cs in cs_list:
        extension_history_factory(
            company=event.company,
            client_subscription=cs,
            added_visits=0,
            date_extended=datetime(2019, 2, 25, tzinfo=pytz.utc),
            extended_from=date(2019, 2, 25),
            extended_to=date(2019, 2, 26),
            related_event=event
        )

    mock = mocker.patch('crm.models.ClientSubscriptions.revoke_extending')

    with freeze_time(date(2019, 2, 26)):
        models.ClientSubscriptions.objects.revoke_extending(event)

    mock.assert_not_called()


def test_manager_revoke_extending_non_canceled(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=None
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event.event_class
    )
    cs_list = client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    for cs in cs_list:
        extension_history_factory(
            company=event.company,
            client_subscription=cs,
            added_visits=0,
            date_extended=datetime(2019, 2, 25, tzinfo=pytz.utc),
            extended_from=date(2019, 2, 25),
            extended_to=date(2019, 2, 26),
            related_event=event
        )

    mock = mocker.patch('crm.models.ClientSubscriptions.revoke_extending')

    with freeze_time(date(2019, 2, 25)):
        models.ClientSubscriptions.objects.revoke_extending(event)

    mock.assert_not_called()


def test_manager_revoke_extending_event_without_extending(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=False
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event.event_class
    )
    cs_list = client_subscription_factory.create_batch(
        3,
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    for cs in cs_list:
        extension_history_factory(
            company=event.company,
            client_subscription=cs,
            added_visits=0,
            date_extended=datetime(2019, 2, 25, tzinfo=pytz.utc),
            extended_from=date(2019, 2, 25),
            extended_to=date(2019, 2, 26),
            related_event=event
        )

    mock = mocker.patch('crm.models.ClientSubscriptions.revoke_extending')

    with freeze_time(date(2019, 2, 25)):
        models.ClientSubscriptions.objects.revoke_extending(event)

    mock.assert_not_called()


def test_revoke_extending_no_chain(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=False
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event.event_class
    )
    cs = client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    ex_his = extension_history_factory(
        company=event.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 25),
        extended_to=date(2019, 2, 26),
        related_event=event
    )
    # Update client subscription end date, as it was changed by extension
    cs.end_date = date(2019, 2, 26)
    cs.save()
    spy = mocker.spy(models.ExtensionHistory, 'delete')

    cs.revoke_extending(event)
    cs.refresh_from_db()

    assert_that(cs.end_date, is_(date(2019, 2, 25)))
    assert_that(
        calling(ex_his.refresh_from_db),
        raises(models.ExtensionHistory.DoesNotExist)
    )
    spy.assert_called_once()


def test_revoke_extending_with_chain(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event_1 = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    event_2 = event_factory(
        company=event_1.company,
        date=date(2019, 2, 26),
        event_class=event_1.event_class,
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    event_3 = event_factory(
        company=event_1.company,
        date=date(2019, 2, 27),
        event_class=event_1.event_class,
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    subs = subscriptions_type_factory(
        company=event_1.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event_1.event_class
    )
    cs = client_subscription_factory(
        company=event_1.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    ex_his_1 = extension_history_factory(
        company=event_1.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, 12, 0, 0, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 25),
        extended_to=date(2019, 2, 26),
        related_event=event_1
    )
    ex_his_2 = extension_history_factory(
        company=event_1.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, 12, 1, 0, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 26),
        extended_to=date(2019, 2, 27),
        related_event=event_2
    )
    ex_his_3 = extension_history_factory(
        company=event_1.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, 12, 2, 0, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 27),
        extended_to=date(2019, 2, 28),
        related_event=event_3
    )
    # Update client subscription end date, as it was changed by extension
    cs.end_date = date(2019, 2, 28)
    cs.save()

    spy = mocker.spy(models.ExtensionHistory, 'delete')
    cs.revoke_extending(event_1)
    cs.refresh_from_db()

    assert_that(cs.end_date, is_(date(2019, 2, 27)))
    assert_that(
        calling(ex_his_1.refresh_from_db),
        raises(models.ExtensionHistory.DoesNotExist)
    )
    ex_his_2.refresh_from_db()
    ex_his_3.refresh_from_db()
    assert_that(ex_his_2, has_properties(
        extended_from=date(2019, 2, 25),
        extended_to=date(2019, 2, 26)
    ))
    assert_that(ex_his_3, has_properties(
        extended_from=date(2019, 2, 26),
        extended_to=date(2019, 2, 27)
    ))
    spy.assert_called_once()


def test_revoke_extending_with_chain_non_ordered(
    subscriptions_type_factory,
    event_factory,
    extension_history_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event_1 = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    event_2 = event_factory(
        company=event_1.company,
        date=date(2019, 2, 26),
        event_class=event_1.event_class,
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    event_3 = event_factory(
        company=event_1.company,
        date=date(2019, 2, 27),
        event_class=event_1.event_class,
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=True
    )
    subs = subscriptions_type_factory(
        company=event_1.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event_1.event_class
    )
    cs = client_subscription_factory(
        company=event_1.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    ex_his_1 = extension_history_factory(
        company=event_1.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, 12, 1, 0, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 26),
        extended_to=date(2019, 2, 27),
        related_event=event_1
    )
    ex_his_2 = extension_history_factory(
        company=event_1.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, 12, 2, 0, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 27),
        extended_to=date(2019, 2, 28),
        related_event=event_2
    )
    ex_his_3 = extension_history_factory(
        company=event_1.company,
        client_subscription=cs,
        added_visits=0,
        date_extended=datetime(2019, 2, 25, 12, 0, 0, tzinfo=pytz.utc),
        extended_from=date(2019, 2, 25),
        extended_to=date(2019, 2, 26),
        related_event=event_3
    )
    # Update client subscription end date, as it was changed by extension
    cs.end_date = date(2019, 2, 28)
    cs.save()

    spy = mocker.spy(models.ExtensionHistory, 'delete')

    cs.revoke_extending(event_1)
    cs.refresh_from_db()

    assert_that(cs.end_date, is_(date(2019, 2, 27)))
    assert_that(
        calling(ex_his_1.refresh_from_db),
        raises(models.ExtensionHistory.DoesNotExist)
    )
    ex_his_2.refresh_from_db()
    ex_his_3.refresh_from_db()
    assert_that(ex_his_2, has_properties(
        extended_from=date(2019, 2, 26),
        extended_to=date(2019, 2, 27)
    ))
    assert_that(ex_his_3, has_properties(
        extended_from=date(2019, 2, 25),
        extended_to=date(2019, 2, 26)
    ))
    spy.assert_called_once()


def test_revoke_extending_no_extension_history(
    subscriptions_type_factory,
    event_factory,
    client_subscription_factory,
    mocker: MockFixture
):
    event = event_factory(
        date=date(2019, 2, 25),
        event_class__date_from=date(2019, 1, 1),
        canceled_at=date(2019, 2, 24),
        canceled_with_extending=False
    )
    subs = subscriptions_type_factory(
        company=event.company,
        duration=1,
        duration_type=GRANULARITY.DAY,
        rounding=False,
        event_class__events=event.event_class
    )
    cs = client_subscription_factory(
        company=event.company,
        subscription=subs,
        purchase_date=date(2019, 2, 24),
        start_date=date(2019, 2, 25)
    )
    spy = mocker.spy(models.ExtensionHistory, 'delete')
    # Update client subscription end date, as it was changed by extension

    cs.revoke_extending(event)

    spy.assert_not_called()
