from datetime import date

import pytest
from hamcrest import assert_that, calling, has_length, is_, raises
from pytest_mock import MockFixture

from crm import models
from crm.events import range_days

pytestmark = pytest.mark.django_db


def test_nearest_infinite_no_days(event_class_factory):
    monday = date(2019, 2, 25)
    ec: models.EventClass = event_class_factory(
        date_from=monday, days=[])

    assert_that(
        ec.days(), is_([])
    )


def test_get_calendar(event_class_factory):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=start, date_to=date(2019, 1, 31))

    assert_that(
        ec.get_calendar(start, date(2019, 1, 31)).values(),
        has_length(31)
    )


def test_get_calendar_to_is_none(event_class_factory):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=start)

    assert_that(
        ec.get_calendar(start, date(2019, 1, 31)).values(),
        has_length(31)
    )


def test_get_calendar_from_is_none(event_class_factory):
    ec = event_class_factory(date_from=None, date_to=date(2019, 1, 10))
    assert_that(
        ec.get_calendar(date(2019, 1, 1), date(2019, 1, 10)).values(),
        has_length(10)
    )


def test_get_calendar_start_is_less_than_event_from(event_class_factory):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=date(2019, 1, 21))

    assert_that(
        ec.get_calendar(start, date(2019, 1, 31)).values(),
        has_length(11)
    )


def test_get_calendar_end_is_greater_than_event_to(event_class_factory):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=start, date_to=date(2019, 1, 10))

    assert_that(
        ec.get_calendar(start, date(2019, 1, 31)).values(),
        has_length(10)
    )


def test_get_calendar_all_absent(
    event_class_factory,
    mocker: MockFixture
):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=start)
    spy = mocker.spy(models, 'Event')

    ec.get_calendar(start, date(2019, 1, 31))
    assert_that(
        spy.call_count, is_(31)
    )


def test_get_calendar_partial_events_exists(
    event_class_factory,
    event_factory,
    mocker: MockFixture
):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=start)
    for day in range_days(start, date(2019, 1, 4)):
        event_factory(
            company=ec.company,
            event_class=ec,
            date=day
        )

    spy = mocker.spy(models, 'Event')

    ec.get_calendar(start, date(2019, 1, 10))
    assert_that(spy.call_count, is_(7))


def test_get_calendar_all_events_exists(
    event_class_factory,
    event_factory,
    mocker: MockFixture
):
    start = date(2019, 1, 1)
    ec = event_class_factory(date_from=start)
    for day in range_days(start, date(2019, 1, 11)):
        event_factory(
            company=ec.company,
            event_class=ec,
            date=day
        )

    spy = mocker.spy(models, 'Event')

    ec.get_calendar(start, date(2019, 1, 10))
    assert_that(spy.call_count, is_(0))
