from datetime import date

from bot.api.messages.base import Message, TemplateItem
from crm.models import ClientSubscriptions


class ClientSubscriptionMessage(Message, abstract=True):
    template_args = {
        'SUBSCRIPTION_NAME': TemplateItem(
            text='Название абонемента',
            example='Базовый месячный'
        ),
        'END_DATE': TemplateItem(
            text='Дата окончания абонемента',
            example=date(2019, 3, 29),
        ),
        'VISITS_LEFT': TemplateItem(
            text='Количество визитов оставшихся на абонементе',
            example=10
        )
    }

    def __init__(
        self,
        recipient,
        personalized=False,
        *,
        clientsub: ClientSubscriptions
    ):
        self.clientsub = clientsub

        super().__init__(recipient, personalized)

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'SUBSCRIPTION_NAME': self.clientsub.subscription.name,
            'END_DATE': self.clientsub.end_date,
            'VISITS_LEFT': self.clientsub.visits_left
        })
        return context


class ClientSubscriptionBuy(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при покупке абонемента'
    default_template = (
        'Вы приобрели абонемент:\n{{SUBSCRIPTION_NAME}}!\n'
        'Действующий до:\n{{END_DATE|date:"d.m.Y"}}'
    )


class ClientSubscriptionVisit(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при посещении занятия'
    default_template = (
        'На вашем абонементе:\n{{SUBSCRIPTION_NAME}}\n'
        'остаток посещений: {{VISITS_LEFT}}'
    )


class ClientSubscriptionExtend(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при продление абонемента'

    default_template = (
        'Вам продлили абонемент:\n{{SUBSCRIPTION_NAME}}\n'
        'Остаток посещений: {{VISITS_LEFT}}'
    )


class ClientUpdateBalance(Message):

    detailed_description = 'Уведомление при изменении баланса клиента'
    default_template = 'Ваш баланс составляет: {{BALANCE}} ₽'
    template_args = {
        'BALANCE': TemplateItem(text='Балас клиента', example=1500)
    }

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'BALANCE': self.recipients[0].get_balance()
        })
        return context
