import pytest
from hamcrest import assert_that, is_, has_properties
from bot.api.commands.hello import HelloCommand
from bot.api.commands.clients import Clients

@pytest.mark.parametrize('msg', ['hello', 'привет'])
def test_hello_command_success(msg):
    command = HelloCommand()

    result_text, _ = command.handle_user_message(msg, 123)

    assert_that(result_text, is_('Привет, друг!\nЯ БОТ, создан для уведомления'))


def test_hello_failed():
    command = HelloCommand()

    result, _ = command.handle_user_message('somebadcommand', 123)

    assert_that(result, is_())


@pytest.mark.parametrize('msg', ['абонементы', 'мои абонементы', 'информация о моих абонементах'])
def test_clients_command_success(msg):
    command = Clients()

    result_text, _ = command.handle_user_message(msg, 123)

    assert_that(result_text, is_('Инфо о ваших абонементах'))
