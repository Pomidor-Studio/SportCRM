from datetime import date, timedelta
from typing import List

import pytest
from freezegun import freeze_time
from hamcrest import (
    assert_that, calling, contains, contains_inanyorder,
    has_properties, is_, raises,
    none,
)
from pytest_mock import MockFixture

from crm import models
from crm.enums import GRANULARITY
from crm.models import (
    ClientSubscriptions, Coach, Location, SubscriptionsType, User,
)

pytestmark = pytest.mark.django_db


def test_user_manager_first_username():
    assert_that(
        User.objects.generate_uniq_username('name', 'test', prefix='coach'),
        is_('coach_0_name_test'))


def test_user_manager_lower():
    assert_that(
        User.objects.generate_uniq_username('Иван', 'Петров', prefix='coach'),
        is_('coach_0_ivan_petrov'))


def test_user_manager_uniq_name_generator(user_factory):
    user_factory(username='coach_0_name_test')
    assert_that(
        User.objects.generate_uniq_username('name', 'test', prefix='coach'),
        is_('coach_1_name_test'))


def test_user_is_not_manager(user_factory):
    user = user_factory()
    assert_that(user.is_manager, is_(False))


def test_user_is_not_coach(user_factory):
    user = user_factory()
    assert_that(user.is_coach, is_(False))


def test_user_is_manager(manager_factory):
    manager = manager_factory()
    assert_that(manager.user, has_properties(
        is_manager=True,
        is_coach=False
    ))


def test_user_is_coach(coach_factory):
    coach = coach_factory()
    assert_that(coach.user, has_properties(
        is_manager=False,
        is_coach=True
    ))


@pytest.mark.parametrize('test_factory, model', [
    (pytest.lazy_fixture('coach_factory'), Coach),
    (pytest.lazy_fixture('location_factory'), Location),
    (pytest.lazy_fixture('subscriptions_type_factory'), SubscriptionsType),
])
def test_item_safe_delete(test_factory, model):
    item = test_factory()
    item.delete()

    count_regular = model.objects.all().count()
    count_all = model.all_objects.all().count()
    count_deleted = model.deleted_objects.all().count()

    assert_that(count_regular, is_(0))
    assert_that(count_all, is_(1))
    assert_that(count_deleted, is_(1))


def test_nearest_event_infinite_no_days(event_class_factory):
    monday = date(2019, 2, 25)
    ec: models.EventClass = event_class_factory(
        date_from=monday, days=[])

    assert_that(
        calling(ec.days),
        raises(ValueError, "Event class don't have any days to spread")
    )


@pytest.mark.parametrize('days', [
    [0, 1, 2, 3, 4, 5, 6],
    [0],
    [6],
    [0, 2, 4],
    [1, 3, 5]
])
def test_gen_calendar_behaviour(days, event_class_factory):
    monday = date(2019, 2, 25)
    last_day = date(2019, 3, 10)
    ec = event_class_factory(date_from=monday, days=days)

    dumb_cal = ec.get_calendar(monday, last_day)
    gen_cal = ec.get_calendar_gen(monday, last_day)

    assert_that(dumb_cal, contains(*gen_cal))


@pytest.mark.parametrize('granularity', [
    GRANULARITY.DAY, GRANULARITY.WEEK, GRANULARITY.MONTH, GRANULARITY.YEAR
])
def test_subscription_start_date_non_rounded(
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
def test_subscription_start_date_rounded(
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
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 3, 1)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 3, 7)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 3, 28)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2020, 2, 28))
])
def test_subscription_end_date_non_rounded(
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
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 3, 1)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 3, 4)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 3, 1)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2020, 1, 1))
])
def test_subscription_end_date_rounded(
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


def test_client_subscription_extend_duration_with_new_end_date(
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


def test_client_subscription_extend_duration_without_new_end_date(
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


def test_client_subscription_extend_duration_without_new_end_date_and_zero(
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


def test_client_subscription_extend_by_cancellation_no_future_date(
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


def test_client_subscription_extend_by_cancellation_with_future_date(
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


def test_client_subscription_qs_active_subscriptions(
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
        ClientSubscriptions.objects.get_queryset().active_subscriptions(event),
        contains_inanyorder(*active_subs)
    )


def test_client_subscriptions_manager_active_subscriptions(
    mocker: MockFixture
):
    mock = mocker.patch(
        'crm.models.ClientSubscriptionQuerySet.active_subscriptions')

    ClientSubscriptions.objects.active_subscriptions(mocker.ANY)

    mock.assert_called_once_with(mocker.ANY)


def test_client_subscriptions_manager_extend_by_cancellation(
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

    ClientSubscriptions.objects.extend_by_cancellation(event)

    assert_that(mock.call_count, is_(3))
    mock.assert_any_call(event)


def test_event_cancel_event_with_extending(
    event_factory,
    mocker: MockFixture
):
    event = event_factory()
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.extend_by_cancellation')
    with freeze_time('2019-02-25'):
        event.cancel_event(extend_subscriptions=True)

    event.refresh_from_db()

    assert_that(event, has_properties(
        canceled_at=date(2019, 2, 25),
        canceled_with_extending=True
    ))
    mock.assert_called_once_with(event)


def test_event_cancel_event_without_extending(
    event_factory,
    mocker: MockFixture
):
    event = event_factory()
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.extend_by_cancellation')
    with freeze_time('2019-02-25'):
        event.cancel_event(extend_subscriptions=False)

    event.refresh_from_db()

    assert_that(event, has_properties(
        canceled_at=date(2019, 2, 25),
        canceled_with_extending=False
    ))
    mock.assert_not_called()


def test_event_cancel_outdated(event_factory):
    event = event_factory(date=date(2019, 2, 24))

    with freeze_time('2019-02-25'):
        assert_that(
            calling(event.cancel_event),
            raises(ValueError, "Event is outdated. It can't be canceled.")
        )


def test_event_cancel_already_cancelled(event_factory):
    event = event_factory(canceled_at=date(2019, 2, 24))

    assert_that(
        calling(event.cancel_event),
        raises(ValueError, "Event is already cancelled.")
    )


def test_event_activate_outdated(event_factory):
    event = event_factory(
        date=date(2019, 2, 24),
        canceled_at=date(2019, 2, 23)
    )

    with freeze_time('2019-02-25'):
        assert_that(
            calling(event.activate_event),
            raises(ValueError, "Event is outdated. It can't be activated.")
        )


def test_event_activate_on_active(event_factory):
    event = event_factory()

    assert_that(
        calling(event.activate_event),
        raises(ValueError, "Event is already in action.")
    )


def test_event_activate_without_revoke_extension(event_factory):
    event = event_factory(
        canceled_at=date(2019, 1, 23)
    )

    event.activate_event()

    event.refresh_from_db()
    assert_that(event, has_properties(
        canceled_at=none(),
        canceled_with_extending=False
    ))


def test_event_activate_with_revoke_extension_but_there_no_was_extending(
    event_factory,
    mocker: MockFixture
):
    event = event_factory(
        canceled_at=date(2019, 1, 23),
        canceled_with_extending=False
    )
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.revoke_extending')

    event.activate_event(revoke_extending=True)

    event.refresh_from_db()
    assert_that(event, has_properties(
        canceled_at=none(),
        canceled_with_extending=False
    ))
    mock.assert_not_called()


def test_event_activate_with_revoke_extension(
    event_factory,
    mocker: MockFixture
):
    event = event_factory(
        canceled_at=date(2019, 1, 23),
        canceled_with_extending=True
    )
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.revoke_extending')

    event.activate_event(revoke_extending=True)

    event.refresh_from_db()
    assert_that(event, has_properties(
        canceled_at=none(),
        canceled_with_extending=False
    ))
    mock.assert_called_once_with(event)
