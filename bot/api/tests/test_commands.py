import pytest
from hamcrest import assert_that, calling, is_, raises

from bot.api.commands.base import InvalidCommand
from bot.api.commands.clients import Clients
from bot.api.commands.hello import HelloCommand

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('msg', ['hello', 'привет'])
def test_hello_command_success(msg):
    command = HelloCommand()

    result_text, _ = command.handle_user_message(msg, 123)

    assert_that(result_text, is_('Привет, друг!\nЯ БОТ, создан для уведомления'))


def test_hello_failed():
    command = HelloCommand()

    assert_that(
        calling(command.handle_user_message).with_args('somebadcommand', 123),
        raises(InvalidCommand)
    )


@pytest.mark.skip()
@pytest.mark.parametrize('msg', [
    'абонементы', 'мои абонементы', 'информация о моих абонементах'
])
def test_clients_command_success(msg):
    command = Clients()

    result_text, _ = command.handle_user_message(msg, 123)

    assert_that(result_text, is_('Инфо о ваших абонементах'))
