from bot.api.messages.base import Message, MessageManager
from crm.models import Event


class ManagerEventMessage(MessageManager):

    def __init__(self, manager, personalized=True, *, event: Event):
        self.event = event

        super().__init__(manager, personalized)


class CancelledEvent(Message):

    def __init__(self, client, personalized=False, *, event: Event):
        self.event = event

        super().__init__(client, personalized)

    def prepare_generalized_msg(self):
        return (
            f'Была отменена тренировка на {self.event.date} '
            f'по {self.event.event_class}'
        )


class ClosedEvent(ManagerEventMessage):

    def prepare_generalized_msg(self):
        return (
            f'Была закрыта тренировка на {self.event.date} '
            f'по {self.event.event_class}\n'
            f'Тренером: {self.event.event_class.coach.user.first_name} {self.event.event_class.coach.user.last_name}'
        )


class OpenedEvent(ManagerEventMessage):

    def prepare_generalized_msg(self):
        return (
            f'Была открыта тренировка на {self.event.date} '
            f'по {self.event.event_class}\n'
            f'Тренером: {self.event.event_class.coach.user.first_name} {self.event.event_class.coach.user.last_name}'
        )
