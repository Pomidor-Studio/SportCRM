from typing import Tuple, Optional
from .base import Command


class HelloCommand(Command):
    keys = ['привет', 'hello', 'дратути', 'здравствуй', 'здравствуйте', 'hi', 'прив']
    description = 'Поприветствую тебя'

    def process(self, user_id: int) -> Tuple[str, Optional[str]]:
        message = 'Привет, друг!\nЯ БОТ, создан для уведомления'
        return message, ''
