from typing import Tuple, Optional
from .base import Command


class Information(Command):
    keys = ['помощь', 'помоги', 'help', 'хелп']
    description = 'Покажу список команд'

    def process(self, user_id: int) -> Tuple[str, Optional[str]]:
        message = []
        message.append('Список команд:\n')
        from . import allowed_commands
        for list in allowed_commands:
            message.extend([list.keys[0], ' - ', list.description, '\n'])
        return ''.join(message), ''
