from datetime import date, timedelta
from typing import List

import pytest
from hamcrest import assert_that, is_, calling, raises

from crm.events import next_day, get_nearest_to, days_delta


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
):
    monday = date(2019, 2, 25)
    request_day = monday + timedelta(days=request_day_delta)

    assert_that(
        get_nearest_to(request_day, days),
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
):
    monday = date(2019, 2, 25)
    end_date = date(2019, 3, 25)
    request_day = monday + timedelta(days=request_day_delta)

    assert_that(
        get_nearest_to(request_day, days, end_date),
        is_(request_day + timedelta(days=expected_delta))
    )


@pytest.mark.parametrize('request_day_delta,days,expected_delta', [
    (0, [0, 1, 2, 3, 4, 5, 6], 1),
    (1, [0, 1, 2, 3, 4, 5, 6], 1),
    (2, [0, 1, 2, 3, 4, 5, 6], 1),
    (3, [0, 1, 2, 3, 4, 5, 6], 1),
    (4, [0, 1, 2, 3, 4, 5, 6], 1),
    (5, [0, 1, 2, 3, 4, 5, 6], 1),

    (0, [0, 3], 3),
    (1, [0, 3], 2),
    (2, [0, 3], 1),
])
def test_nearest_event_to_finite_last_week(
    request_day_delta: int,
    days: List[int],
    expected_delta: int,
):
    monday = date(2019, 2, 25)
    end_date = monday + timedelta(days=6)
    request_day = monday + timedelta(days=request_day_delta)

    assert_that(
        get_nearest_to(request_day, days, end_date),
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
):
    monday = date(2019, 2, 25)
    end_date = monday + timedelta(days=6)
    request_day = monday + timedelta(days=request_day_delta)

    assert_that(
        calling(get_nearest_to).with_args(request_day, days, end_date),
        raises(ValueError, exc_msg)
    )


@pytest.mark.parametrize('input_days,expected', [
    ([0, 1, 2, 3, 4, 5, 6], [1, 1, 1, 1, 1, 1, 1]),
    ([0], [7]),
    ([1], [7]),
    ([2], [7]),
    ([3], [7]),
    ([4], [7]),
    ([5], [7]),
    ([6], [7]),
    ([0, 2, 4], [2, 2, 3]),
    ([1, 3, 5], [2, 2, 3]),
    ([0, 6], [6, 1]),
    ([1, 6], [5, 2]),
    ([5, 6], [1, 6]),
    ([], [])
])
def test_days_delta(input_days, expected):
    assert_that(days_delta(input_days), is_(expected))


@pytest.mark.parametrize('start,stop,days,expected', [
    (
        date(2019, 2, 25),
        date(2019, 3, 3),
        [0, 1, 2, 3, 4, 5, 6],
        [date(2019, 2, 25) + timedelta(days=x) for x in range(7)]
    ),
    (
        date(2019, 2, 25),
        date(2019, 3, 10),
        [0, 1, 2, 3, 4, 5, 6],
        [date(2019, 2, 25) + timedelta(days=x) for x in range(14)]
    ),
    (
        date(2019, 2, 25),
        date(2019, 3, 24),
        [0],
        [date(2019, 2, 25) + timedelta(days=7 * x) for x in range(4)]
    ),
    (
        date(2019, 2, 25),
        date(2019, 3, 24),
        [6],
        [date(2019, 3, 3) + timedelta(days=7 * x) for x in range(4)]
    ),
    (
        date(2019, 2, 25),
        date(2019, 3, 10),
        [0, 1],
        [
            date(2019, 2, 25), date(2019, 2, 26),
            date(2019, 3, 4), date(2019, 3, 5)
        ]
    ),
    (
        date(2019, 2, 25),
        date(2019, 3, 10),
        [1, 2],
        [
            date(2019, 2, 26), date(2019, 2, 27),
            date(2019, 3, 5), date(2019, 3, 6)
        ]
    ),
    (
        date(2019, 2, 25),
        date(2019, 3, 10),
        [1, 3, 5],
        [
            date(2019, 2, 26), date(2019, 2, 28), date(2019, 3, 2),
            date(2019, 3, 5), date(2019, 3, 7), date(2019, 3, 9),
        ]
    ),
])
def test_next_day(start, stop, days, expected):
    assert_that(list(next_day(start, stop, days)), is_(expected))
