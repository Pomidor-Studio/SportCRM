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
