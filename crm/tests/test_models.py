import pytest
from hamcrest import assert_that, is_

pytestmark = pytest.mark.django_db


def test_is_not_manager(user_factory):
    user = user_factory()
    assert_that(user.is_manager, is_(False))


def test_is_not_coach(user_factory):
    user = user_factory()
    assert_that(user.is_coach, is_(False))
