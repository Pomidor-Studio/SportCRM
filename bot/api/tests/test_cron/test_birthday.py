from datetime import date

import pytest
from django_multitenant.utils import set_current_tenant
from hamcrest import assert_that, is_
from freezegun import freeze_time
from pytest_mock import MockFixture

from bot.api.cron.cron_client_events import birthday

pytestmark = pytest.mark.django_db


def test_empty_list(
    company_factory,
    client_factory,
    mocker: MockFixture
):
    companies = company_factory.create_batch(3)
    for company in companies:
        client_factory.create_batch(
            3, birthday=date(2019, 1, 2), company=company)

    mock_user_to_user = mocker.patch(
        'bot.api.cron.cron_client_events.UserToUserBirthday')
    mock_users_to_manager = mocker.patch(
        'bot.api.cron.cron_client_events.UsersToManagerBirthday')
    with freeze_time(date(2019, 1, 1)):
        birthday()

    mock_user_to_user.assert_not_called()
    mock_users_to_manager.assert_not_called()


def test_one_company_with_birthday(
    company_factory,
    client_factory,
    manager_factory,
    mocker: MockFixture
):
    companies = company_factory.create_batch(3)
    # Reset current tenant, as factories set in internally
    set_current_tenant(None)
    for idx, company in enumerate(companies):
        client_factory.create_batch(
            3, birthday=date(2019, 1, idx + 1), company=company)
        manager_factory.create_batch(3, user__company=company)

    mock_user_to_user = mocker.patch(
        'bot.api.cron.cron_client_events.UserToUserBirthday', autospec=True)
    mock_users_to_manager = mocker.patch(
        'bot.api.cron.cron_client_events.UsersToManagerBirthday', autospec=True)

    with freeze_time(date(2019, 1, 1)):
        birthday()

    assert_that(mock_user_to_user.call_count, is_(1))
    assert_that(mock_users_to_manager.call_count, is_(1))


def test_all_companies_with_birthday(
    company_factory,
    client_factory,
    manager_factory,
    mocker: MockFixture
):
    companies = company_factory.create_batch(3)
    # Reset current tenant, as factories set in internally
    set_current_tenant(None)
    for company in companies:
        client_factory.create_batch(
            3, birthday=date(2019, 1, 1), company=company)
        manager_factory.create_batch(3, user__company=company)

    mock_user_to_user = mocker.patch(
        'bot.api.cron.cron_client_events.UserToUserBirthday', autospec=True)
    mock_users_to_manager = mocker.patch(
        'bot.api.cron.cron_client_events.UsersToManagerBirthday', autospec=True)

    with freeze_time(date(2019, 1, 1)):
        birthday()

    assert_that(mock_user_to_user.call_count, is_(3))
    assert_that(mock_users_to_manager.call_count, is_(3))
