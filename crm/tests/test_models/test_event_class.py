from datetime import date

import pytest
from hamcrest import (
    assert_that, calling, contains, raises,
)

from crm import models

pytestmark = pytest.mark.django_db


def test_nearest_infinite_no_days(event_class_factory):
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
