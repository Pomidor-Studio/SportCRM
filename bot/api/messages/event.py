from bot.api.messages.base import Message
from crm.models import Event


class CancelledEvent(Message):

    detailed_description = 'Уведомление при отмене тренировки'

    def __init__(self, client, personalized=False, *, event: Event):
        self.event = event

        super().__init__(client, personalized)

    def prepare_generalized_msg(self):
        return (
            f'Была отменена тренировка на {self.event.date} '
            f'по {self.event.event_class}'
        )
