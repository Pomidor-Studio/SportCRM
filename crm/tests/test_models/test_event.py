from datetime import date

import pytest
from freezegun import freeze_time
from hamcrest import (assert_that, calling, has_properties, none, raises)
from pytest_mock import MockFixture

pytestmark = pytest.mark.django_db


def test_cancel_with_extending(
    event_factory,
    mocker: MockFixture
):
    event = event_factory()
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.extend_by_cancellation')
    mock_google_tasks = mocker.patch('gcp.tasks.enqueue')
    with freeze_time('2019-02-25'):
        event.cancel_event(extend_subscriptions=True)

    event.refresh_from_db()

    assert_that(event, has_properties(
        canceled_at=date(2019, 2, 25),
        canceled_with_extending=True
    ))
    mock.assert_called_once_with(event)
    mock_google_tasks.assert_called_once_with('notify_event_cancellation', event.id)


def test_cancel_without_extending(
    event_factory,
    mocker: MockFixture
):
    event = event_factory()
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.extend_by_cancellation')
    mock_google_tasks = mocker.patch('gcp.tasks.enqueue')
    with freeze_time('2019-02-25'):
        event.cancel_event(extend_subscriptions=False)

    event.refresh_from_db()

    assert_that(event, has_properties(
        canceled_at=date(2019, 2, 25),
        canceled_with_extending=False
    ))
    mock.assert_not_called()
    mock_google_tasks.assert_called_once_with('notify_event_cancellation', event.id)


def test_cancel_outdated(event_factory):
    event = event_factory(date=date(2019, 2, 24))

    with freeze_time('2019-02-25'):
        assert_that(
            calling(event.cancel_event),
            raises(ValueError, "Event is outdated. It can't be canceled.")
        )


def test_cancel_already_cancelled(event_factory):
    event = event_factory(canceled_at=date(2019, 2, 24))

    assert_that(
        calling(event.cancel_event),
        raises(ValueError, "Event is already cancelled.")
    )


def test_activate_outdated(event_factory):
    event = event_factory(
        date=date(2019, 2, 24),
        canceled_at=date(2019, 2, 23)
    )

    with freeze_time('2019-02-25'):
        assert_that(
            calling(event.activate_event),
            raises(ValueError, "Event is outdated. It can't be activated.")
        )


def test_activate_on_active(event_factory):
    event = event_factory()

    assert_that(
        calling(event.activate_event),
        raises(ValueError, "Event is already in action.")
    )


def test_activate_without_revoke_extension(event_factory):
    event = event_factory(
        canceled_at=date(2019, 1, 23)
    )

    event.activate_event()

    event.refresh_from_db()
    assert_that(event, has_properties(
        canceled_at=none(),
        canceled_with_extending=False
    ))


def test_activate_with_revoke_extension_but_there_no_was_extending(
    event_factory,
    mocker: MockFixture
):
    event = event_factory(
        canceled_at=date(2019, 1, 23),
        canceled_with_extending=False
    )
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.revoke_extending')

    event.activate_event(revoke_extending=True)

    event.refresh_from_db()
    assert_that(event, has_properties(
        canceled_at=none(),
        canceled_with_extending=False
    ))
    mock.assert_not_called()


def test_activate_with_revoke_extension(
    event_factory,
    mocker: MockFixture
):
    event = event_factory(
        canceled_at=date(2019, 1, 23),
        canceled_with_extending=True
    )
    mock = mocker.patch(
        'crm.models.ClientSubscriptionsManager.revoke_extending')

    event.activate_event(revoke_extending=True)

    event.refresh_from_db()
    assert_that(event, has_properties(
        canceled_at=none(),
        canceled_with_extending=False
    ))
    mock.assert_called_once_with(event)
