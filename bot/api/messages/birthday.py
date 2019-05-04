from operator import attrgetter
from typing import List

from bot.api.messages.base import Message, TemplateItem, RecipientTypes
from crm.models import Client


class UserToUserBirthday(Message):
    detailed_description = 'Поздравление клиента с днем рождения'
    default_template = 'Поздравляем вас с Днем рождения!'
    recipient = RecipientTypes.client


class UsersToManagerBirthday(Message):
    detailed_description = 'Уведомление менеджеру о днях рождения клиентов'
    default_template = 'Сегодня день рождения у\n{{CLIENTS}}'
    recipient = RecipientTypes.manager
    template_args = {
        'CLIENTS': TemplateItem(
            text='Список учеников, у которых сегодня день рождения',
            example='1. Иванов Иван\n2. Петров Петр\n3. Сидоров Сидор'
        )
    }

    def __init__(self, recipient, personalized=False, *, clients: List[Client]):
        self.clients = sorted(clients, key=attrgetter('name'))

        super().__init__(recipient, personalized)

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'CLIENTS': '\n'.join(
                f'{idx}. {client.name}'
                for idx, client in enumerate(self.clients)
            ),
        })
        return context
