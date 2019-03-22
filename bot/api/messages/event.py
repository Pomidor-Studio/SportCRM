from datetime import date

from bot.api.messages.base import Message, TemplateItem
from crm.models import Event


class CancelledEvent(Message):

    detailed_description = 'Уведомление при отмене тренировки'
    default_template = (
        'Была отменена тренировка на {{DATE|date:"d.m.Y"}} по {{NAME}}'
    )
    template_args = {
        'DATE': TemplateItem(
            text='Дата тренировки, в формате ДД.ММ.ГГГГ',
            example=date(2019, 2, 12)
        ),
        'NAME': TemplateItem(text='Название тренировки', example='Волейбол')
    }

    def __init__(self, recipient, personalized=False, *, event: Event):
        self.event = event

        super().__init__(recipient, personalized)

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'DATE': self.event.date,
            'NAME': self.event.event_class
        })
        return context
