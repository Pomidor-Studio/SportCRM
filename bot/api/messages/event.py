from datetime import date

from bot.api.messages.base import Message, TemplateItem, RecipientTypes
from crm.models import Event, Client


class EventMessage(Message, abstract=True):
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
        'CLIENTS_COUNT': TemplateItem(
            text='Количество посетивших тренировку',
            example=50
        )
    }

    def __init__(self, recipient, personalized=False, *, event: Event):
        self.event = event

        super().__init__(recipient, personalized)

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'DATE': self.event.date,
            'NAME': self.event.event_class,
            'COACH': self.event.event_class.coach.user.get_full_name(),
            'CLIENTS_COUNT': self.event.get_present_clients_count()
        })
        return context


class CancelledEvent(EventMessage):
    detailed_description = 'Уведомление ученику при отмене тренировки'
    default_template = (
        'Была отменена тренировка на {{DATE|date:"d.m.Y"}} по {{NAME}}'
    )
    recipient = RecipientTypes.client


class ClosedEvent(EventMessage):
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
        'CLIENTS_COUNT': TemplateItem(
            text='Количество посетивших тренировку',
            example=50
        ),
        'CLIENTS_COUNT_ONE_TIME_SUB': TemplateItem(
            text='Количество посетивших тренировку по одноразовому абонименту',
            example=3
        ),
        'PROFIT': TemplateItem(
            text='Сумма проданных на тренировке абониментов',
            example=1099
        ),
        'SALES_COUNT': TemplateItem(
            text='Количество проданных на тренировке абониментов',
            example=5
        ),
    }
    recipient = RecipientTypes.manager

    default_template = (
        'Была закрыта тренировка на {{DATE|date:"d.m.Y"}} по {{NAME}}\n'
        'Тренером: {{COACH}}\n'
        'Количество посетивших: {{CLIENTS_COUNT}}\n'
        'По одноразовому абонименту: {{CLIENTS_COUNT_ONE_TIME_SUB}}\n'
        'Количество проданных абониментов: {{SALES_COUNT}}\n'
        'Сумма проданных абониментов: {{PROFIT}}'
    )

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'CLIENTS_COUNT': self.event.get_present_clients_count(),
            'CLIENTS_COUNT_ONE_TIME_SUB': self.event.get_clients_count_one_time_sub(),
            'PROFIT': self.event.get_profit(),
            'SALES_COUNT': self.event.get_subs_sales(),
        })
        return context


class OpenedEvent(EventMessage):
    detailed_description = 'Уведомление менеджеру при открытии тренировки'
    recipient = RecipientTypes.manager
    default_template = (
        'Была открыта тренировка на {{DATE|date:"d.m.Y"}} по {{NAME}}\n'
        'Тренером: {{COACH}}'
    )


class ManagerEventMessage(EventMessage, abstract=True):
    recipient = RecipientTypes.manager
    template_args = {
        **EventMessage.template_args,
        'CLIENT': TemplateItem(
            text='Клиент который записался на тренировку',
            example='Иванов Иван'
        )
    }

    def __init__(
        self, recipient, personalized=False, *, event: Event, client: Client
    ):
        self.client = client

        super().__init__(recipient, personalized, event=event)

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'CLIENT': self.client.name
        })
        return context


class SignupClient(ManagerEventMessage):
    detailed_description = 'Уведомление менеджеру о записи на тренировку'
    default_template = (
        '{{CLIENT}} записался на {{NAME}} - {{DATE|date:"d.m.Y"}}'
    )


class UnsignupClient(ManagerEventMessage):
    detailed_description = (
        'Уведомление менеджеру об отмене записи на тренировку'
    )
    default_template = (
        '{{CLIENT}} отмнил запись на {{NAME}} - {{DATE|date:"d.m.Y"}}'
    )
