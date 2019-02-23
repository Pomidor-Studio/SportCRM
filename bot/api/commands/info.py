from typing import Tuple, Optional
from .base import Command
from .commands_list import commands_list


class Information(Command):
    keys = ['помощь', 'помоги', 'help', 'хелп']
    description = 'Покажу список команд'

    def process(self, user_id: int) -> Tuple[str, Optional[str]]:
        message = []
        message.append('Список команд:\n')
        for list in commands_list:
            message.extend([list.keys[0], ' - ', list.description, '\n'])
        return ''.join(message), ''
