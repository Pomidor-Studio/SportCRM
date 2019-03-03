import pytest
from hamcrest import assert_that, calling, contains, has_length, is_, raises
from pytest_mock import MockFixture

from bot.api.messages.base import Message

pytestmark = pytest.mark.django_db


def test_message_init_single(client_factory):
    client = client_factory()
    msg_sender = Message(client)

    assert_that(msg_sender.clients, contains(client))


def test_message_init_multiple(client_factory):
    clients = client_factory.create_batch(3)

    msg_sender = Message(clients)

    assert_that(msg_sender.clients, contains(*clients))


def test_message_init_empty_list():
    msg_sender = Message([])

    assert_that(msg_sender.clients, has_length(0))


@pytest.mark.parametrize('wrong_val', [
    None,
    'TEST-STR',
    dict(),
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
    pgm = mocker.patch('bot.api.messages.base.Message.prepare_generalized_msg')
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
        'bot.api.messages.base.Message.prepare_generalized_msg',
        return_value='Test'
    )
    sm = mocker.patch('bot.api.messages.base.send_message')
    msg_sender = Message(client_factory())
    msg_sender.send_message()

    sm.assert_not_called()


def test_send(client_factory, mocker: MockFixture):
    mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_msg',
        return_value='Test'
    )
    sm = mocker.patch('bot.api.messages.base.send_message')
    msg_sender = Message(client_factory(vk_user_id=1))
    msg_sender.send_message()

    sm.assert_called_once_with(1, mocker.ANY, 'Test')


def test_send_personalized(client_factory, mocker: MockFixture):
    client = client_factory(vk_user_id=1)
    mocker.patch(
        'bot.api.messages.base.Message.prepare_generalized_msg',
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
        'bot.api.messages.base.Message.prepare_generalized_msg',
        return_value='Test'
    )

    msg_sender = Message(client, personalized=True)

    spy = mocker.spy(msg_sender, 'personalize')
    sm = mocker.patch('bot.api.messages.base.send_message')

    msg_sender.send_message()

    assert_that(spy.call_count, is_(3))
    assert_that(sm.call_count, is_(3))
