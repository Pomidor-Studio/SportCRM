from datetime import date, timedelta
from typing import List

import pytest
from hamcrest import assert_that, is_, has_properties, calling, raises

from crm import models
from crm.models import User, Coach, Location, SubscriptionsType

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


@pytest.mark.parametrize('request_day_delta,days,expected_delta', [
    (0, [0, 1, 2, 3, 4, 5, 6], 1),
    (1, [0, 1, 2, 3, 4, 5, 6], 1),
    (2, [0, 1, 2, 3, 4, 5, 6], 1),
    (3, [0, 1, 2, 3, 4, 5, 6], 1),
    (4, [0, 1, 2, 3, 4, 5, 6], 1),
    (5, [0, 1, 2, 3, 4, 5, 6], 1),
    (6, [0, 1, 2, 3, 4, 5, 6], 1),

    (0, [0], 7),
    (1, [0], 6),
    (2, [0], 5),
    (3, [0], 4),
    (4, [0], 3),
    (5, [0], 2),
    (6, [0], 1),

    (0, [0, 3], 3),
    (1, [0, 3], 2),
    (2, [0, 3], 1),
    (3, [0, 3], 4),
    (4, [0, 3], 3),
    (5, [0, 3], 2),
    (6, [0, 3], 1),
])
def test_nearest_event_to_infinite_event(
    request_day_delta: int,
    days: List[int],
    expected_delta: int,
    event_class_factory
):
    monday = date(2019, 2, 25)
    request_day = monday + timedelta(days=request_day_delta)
    ec: models.EventClass = event_class_factory(date_from=monday, days=days)

    assert_that(
        ec.get_nearest_event_to(request_day),
        is_(request_day + timedelta(days=expected_delta))
    )


@pytest.mark.parametrize('request_day_delta,days,expected_delta', [
    (0, [0, 1, 2, 3, 4, 5, 6], 1),
    (1, [0, 1, 2, 3, 4, 5, 6], 1),
    (2, [0, 1, 2, 3, 4, 5, 6], 1),
    (3, [0, 1, 2, 3, 4, 5, 6], 1),
    (4, [0, 1, 2, 3, 4, 5, 6], 1),
    (5, [0, 1, 2, 3, 4, 5, 6], 1),
    (6, [0, 1, 2, 3, 4, 5, 6], 1),

    (0, [0], 7),
    (1, [0], 6),
    (2, [0], 5),
    (3, [0], 4),
    (4, [0], 3),
    (5, [0], 2),
    (6, [0], 1),

    (0, [0, 3], 3),
    (1, [0, 3], 2),
    (2, [0, 3], 1),
    (3, [0, 3], 4),
    (4, [0, 3], 3),
    (5, [0, 3], 2),
    (6, [0, 3], 1),
])
def test_nearest_event_to_finite_event(
    request_day_delta: int,
    days: List[int],
    expected_delta: int,
    event_class_factory
):
    monday = date(2019, 2, 25)
    request_day = monday + timedelta(days=request_day_delta)
    ec: models.EventClass = event_class_factory(
        date_from=monday, date_to=date(2019, 3, 25), days=days)

    assert_that(
        ec.get_nearest_event_to(request_day),
        is_(request_day + timedelta(days=expected_delta))
    )


@pytest.mark.parametrize('request_day_delta,days,expected_delta', [
    (0, [0, 1, 2, 3, 4, 5, 6], 1),
    (1, [0, 1, 2, 3, 4, 5, 6], 1),
    (2, [0, 1, 2, 3, 4, 5, 6], 1),
    (3, [0, 1, 2, 3, 4, 5, 6], 1),
    (4, [0, 1, 2, 3, 4, 5, 6], 1),
    (5, [0, 1, 2, 3, 4, 5, 6], 1),
    pytest.param(
        6, [0, 1, 2, 3, 4, 5, 6], 1,
        marks=pytest.mark.xfail(raises=ValueError)
    ),

    pytest.param(0, [0], 7, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(1, [0], 6, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(2, [0], 5, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(3, [0], 4, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(4, [0], 3, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(5, [0], 2, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(6, [0], 1, marks=pytest.mark.xfail(raises=ValueError)),

    (0, [0, 3], 3),
    (1, [0, 3], 2),
    (2, [0, 3], 1),
    pytest.param(3, [0, 3], 4, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(4, [0, 3], 3, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(5, [0, 3], 2, marks=pytest.mark.xfail(raises=ValueError)),
    pytest.param(6, [0, 3], 1, marks=pytest.mark.xfail(raises=ValueError)),
])
def test_nearest_event_to_finite_last_week(
    request_day_delta: int,
    days: List[int],
    expected_delta: int,
    event_class_factory
):
    monday = date(2019, 2, 25)
    request_day = monday + timedelta(days=request_day_delta)
    ec: models.EventClass = event_class_factory(
        date_from=monday, date_to=monday + timedelta(days=6), days=days)

    assert_that(
        ec.get_nearest_event_to(request_day),
        is_(request_day + timedelta(days=expected_delta))
    )


@pytest.mark.parametrize('request_day_delta,days,exc_msg', [
    (6, [0, 1, 2, 3, 4, 5, 6], "Can't find next event for date in future"),

    (0, [0], "Required day is out of event class date range"),
    (1, [0], "Required day is out of event class date range"),
    (2, [0], "Required day is out of event class date range"),
    (3, [0], "Required day is out of event class date range"),
    (4, [0], "Required day is out of event class date range"),
    (5, [0], "Required day is out of event class date range"),
    (6, [0], "Can't find next event for date in future"),

    (3, [0, 3], "Required day is out of event class date range"),
    (4, [0, 3], "Required day is out of event class date range"),
    (5, [0, 3], "Required day is out of event class date range"),
    (6, [0, 3], "Can't find next event for date in future"),
])
def test_nearest_event_to_finite_last_week_error(
    request_day_delta: int,
    days: List[int],
    exc_msg: str,
    event_class_factory
):
    monday = date(2019, 2, 25)
    request_day = monday + timedelta(days=request_day_delta)
    ec: models.EventClass = event_class_factory(
        date_from=monday, date_to=monday + timedelta(days=6), days=days)

    assert_that(
        calling(ec.get_nearest_event_to).with_args(request_day),
        raises(ValueError, exc_msg)
    )


def test_nearest_event_infinite_no_days(event_class_factory):
    monday = date(2019, 2, 25)
    request_day = monday + timedelta(3)
    ec: models.EventClass = event_class_factory(
        date_from=monday, days=[])

    assert_that(
        calling(ec.get_nearest_event_to).with_args(request_day),
        raises(ValueError, "Event class don't have any days to spread")
    )
