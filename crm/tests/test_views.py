import pytest
from django.urls import reverse
from hamcrest import assert_that

from crm.tests.matchers import (
    is_http_200_response, is_http_302_response, is_http_403_response,
)

pytestmark = pytest.mark.django_db


def test_anonymous_login(client):
    path = reverse('crm:accounts:login')
    response = client.get(path)

    assert_that(response, is_http_200_response())


@pytest.mark.parametrize('path', [
    'crm:manager:event:calendar',
    'crm:manager:client:list',
    'crm:manager:client:new',
    'crm:manager:subscription:list',
    'crm:manager:coach:new',
    'crm:manager:coach:list',
    'crm:manager:event-class:list',
])
def test_manager_urls_for_non_loged(path, client):
    response = client.get(reverse(path))

    assert_that(response, is_http_302_response())


@pytest.mark.parametrize('path', [
    'crm:manager:client:new',
    'crm:manager:subscription:list',
    'crm:manager:coach:new',
    'crm:manager:coach:list',
    'crm:manager:event-class:list',
])
def test_manager_urls_for_coach(path, client, coach_factory):
    coach = coach_factory()
    client.login(username=coach.user.username, password='defaultpassword')

    response = client.get(reverse(path))

    assert_that(response, is_http_403_response())
