import pytest
from hamcrest import assert_that, is_

from crm.models import Coach, Location, SubscriptionsType


pytestmark = pytest.mark.django_db


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
