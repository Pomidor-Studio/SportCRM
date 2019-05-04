from datetime import date

from bot.api.messages.base import Message, TemplateItem, RecipientTypes
from crm.models import EventClass


class EventClassMessage(Message, abstract=True):
    recipient = RecipientTypes.client
    template_args = {
        'DATE': TemplateItem(
            text='Дата тренировки, в формате ДД.ММ.ГГГГ',
            example=date(2019, 2, 12)
        ),
        'NAME': TemplateItem(text='Название тренировки', example='Волейбол'),
        'COACH': TemplateItem(
            text='Тренер',
            example='Крылов Михаил Дмитриевич'
        ),
    }

    def __init__(self, recipient, personalized=False, *, date, event_class: EventClass):
        self.event_class = event_class
        self.date = date

        super().__init__(recipient, personalized)

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'DATE': self.date,
            'NAME': self.event_class,
            'COACH': self.event_class.coach.user.get_full_name(),
        })
        return context


class FutureEvent(EventClassMessage):

    detailed_description = (
        'Уведомление клиенту о предстоящей тренировке'
    )
    default_template = (
        '{{DATE|date:"d.m.Y"}} у Вас предстоит тренировка по {{NAME}}\n'
        'Тренер: {{COACH}}'
    )


class LastFutureEvent(EventClassMessage):

    detailed_description = (
        'Уведомление клиенту о последней запланированной тренировке'
    )
    default_template = (
        '{{DATE|date:"d.m.Y"}} у Вас предстоит тренировка по {{NAME}}.\n'
        'Тренер: {{COACH}}\n\n'
        'Напоминаем, что после этого занятия действие абонемента заканчивается.'
    )
