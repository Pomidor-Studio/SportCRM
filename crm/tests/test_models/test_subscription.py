from datetime import date

import pytest
from hamcrest import assert_that, is_

from crm.enums import GRANULARITY

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
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 3, 1)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 3, 7)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 3, 28)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2020, 2, 28))
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
    (GRANULARITY.DAY, date(2019, 2, 28), date(2019, 3, 1)),
    (GRANULARITY.WEEK, date(2019, 2, 28), date(2019, 3, 4)),
    (GRANULARITY.MONTH, date(2019, 2, 28), date(2019, 3, 1)),
    (GRANULARITY.YEAR, date(2019, 2, 28), date(2020, 1, 1))
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
