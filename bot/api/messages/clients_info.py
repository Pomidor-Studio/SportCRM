from datetime import date

from bot.api.messages.base import Message, TemplateItem, RecipientTypes
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
        ),
        'PRICE': TemplateItem(
            text='Стоимость абонемента',
            example=5000
        )
    }
    recipient = RecipientTypes.client

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
            'VISITS_LEFT': self.clientsub.visits_left,
            'PRICE': self.clientsub.subscription.price
        })
        return context


class ClientSubscriptionBuy(ClientSubscriptionMessage):

    detailed_description = 'Уведомление ученику при покупке абонемента'
    default_template = (
        'Вы приобрели абонемент:\n{{SUBSCRIPTION_NAME}}!\n'
        'Стоимостью: {{PRICE}} ₽\n'
        'Действующий до:\n{{END_DATE|date:"d.m.Y"}}'
    )


class ClientSubscriptionVisit(ClientSubscriptionMessage):

    detailed_description = 'Уведомление ученику при посещении занятия'
    default_template = (
        'На вашем абонементе:\n{{SUBSCRIPTION_NAME}}\n'
        'остаток посещений: {{VISITS_LEFT}}'
    )


class ClientSubscriptionExtend(ClientSubscriptionMessage):

    detailed_description = 'Уведомление ученику при продление абонемента'

    default_template = (
        'Вам продлили абонемент:\n{{SUBSCRIPTION_NAME}}\n'
        'Остаток посещений: {{VISITS_LEFT}}'
    )


class ClientUpdateBalance(Message):

    detailed_description = 'Уведомление ученику при изменении баланса'
    default_template = 'Ваш баланс составляет: {{BALANCE}} ₽'
    template_args = {
        'BALANCE': TemplateItem(text='Балас клиента', example=1500)
    }
    recipient = RecipientTypes.client

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'BALANCE': self.recipients[0].get_balance()
        })
        return context


class ClientHaveNegativeBalance(Message):
    """
    Currently can't be used with list of clients. It can accept only
    one client as recipient
    """
    detailed_description = 'Уведомление ученику при отрицательном балансе'
    default_template = (
        'У вас есть задолженность!\n'
        'Ваш баланс составляет: {{BALANCE}} ₽'
    )
    template_args = {
        'BALANCE': TemplateItem(text='Балас клиента', example=-1500)
    }
    recipient = RecipientTypes.client

    def get_template_context(self):
        context = super().get_template_context()
        context.update({
            'BALANCE': self.recipients[0].get_balance()
        })
        return context
