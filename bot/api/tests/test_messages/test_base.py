import pytest
from hamcrest import (
    assert_that, calling, contains, contains_inanyorder,
    has_length, is_, raises,
)
from pytest_mock import MockFixture

from bot.api.messages.base import Message

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('recipient_factory', [
    pytest.lazy_fixture('coach_factory'),
    pytest.lazy_fixture('manager_factory'),
    pytest.lazy_fixture('client_factory')
])
def test_init_single(recipient_factory):
    recipient = recipient_factory()
    msg_sender = Message(recipient)

    assert_that(msg_sender.recipients, contains(recipient))


def test_init_multiple_same_class(client_factory):
    clients = client_factory.create_batch(3)

    msg_sender = Message(clients)

    assert_that(msg_sender.recipients, contains(*clients))


def test_init_multiple_filtered(
    client_factory,
    coach_factory,
    manager_factory
):
    client = client_factory()
    manager = manager_factory()
    coach = coach_factory()

    msg_sender = Message([client, manager, coach, 1, 'str', None])

    assert_that(
        msg_sender.recipients,
        contains_inanyorder(client, manager, coach)
    )


def test_message_init_empty_list():
    msg_sender = Message([])

    assert_that(msg_sender.recipients, has_length(0))


@pytest.mark.parametrize('wrong_val', [
    None,
    10
])
def test_message_init_with_wrong_value(wrong_val):
    assert_that(
        calling(Message).with_args(wrong_val),
        raises(ValueError, 'Invalid client argument passed')
    )


def test_personalize(client_factory):
    client = client_factory()

    msg_sender = Message(client)
    personalized_msg = msg_sender.personalize('Test', client)

    assert_that(personalized_msg, is_(f'{client.name}, test'))


def test_send_message_empty_list(mocker: MockFixture):
    pgm = mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_message')
    sm = mocker.patch('bot.api.vkapi.send_message')

    msg_sender = Message([])
    msg_sender.send_message()

    pgm.assert_not_called()
    sm.assert_not_called()


def test_send_empty_message(client_factory, mocker: MockFixture):
    sm = mocker.patch('bot.api.vkapi.send_message')
    msg_sender = Message(client_factory())
    msg_sender.send_message()

    sm.assert_not_called()


def test_send_to_non_vk_user(client_factory, mocker: MockFixture):
    mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_message',
        return_value='Test'
    )
    sm = mocker.patch('bot.api.messages.base.send_message')
    msg_sender = Message(client_factory())
    msg_sender.send_message()

    sm.assert_not_called()


def test_send(client_factory, mocker: MockFixture):
    mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_message',
        return_value='Test'
    )
    sm = mocker.patch('bot.api.messages.base.send_message')
    msg_sender = Message(client_factory(vk_user_id=1))
    msg_sender.send_message()

    sm.assert_called_once_with(1, mocker.ANY, 'Test')


def test_send_personalized(client_factory, mocker: MockFixture):
    client = client_factory(vk_user_id=1)
    mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_message',
        return_value='Test'
    )

    msg_sender = Message(client, personalized=True)

    spy = mocker.spy(msg_sender, 'personalize')
    sm = mocker.patch('bot.api.messages.base.send_message')

    msg_sender.send_message()

    spy.assert_called_once_with('Test', client)
    sm.assert_called_once_with(1, mocker.ANY, mocker.ANY)


def test_send_personalized_multiple(client_factory, mocker: MockFixture):
    client = client_factory.create_batch(3, vk_user_id=1)
    mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_message',
        return_value='Test'
    )

    msg_sender = Message(client, personalized=True)

    spy = mocker.spy(msg_sender, 'personalize')
    sm = mocker.patch('bot.api.messages.base.send_message')

    msg_sender.send_message()

    assert_that(spy.call_count, is_(3))
    assert_that(sm.call_count, is_(3))
