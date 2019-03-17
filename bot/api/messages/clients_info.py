from bot.api.messages.base import Message
from crm.models import ClientSubscriptions


class ClientSubscriptionMessage(Message, abstract=True):

    def __init__(
        self,
        recipient,
        personalized=False,
        *,
        clientsub: ClientSubscriptions
    ):
        self.clientsub = clientsub

        super().__init__(recipient, personalized)


class ClientSubscriptionBuy(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при покупке абонемента'

    def prepare_generalized_message(self):
        return (
            f'Вы приобрели абонемент:\n'
            f'{self.clientsub.subscription.name}!\n'
            f'Действующий до:\n{self.clientsub.end_date:%d.%m.%Y}'
        )


class ClientSubscriptionVisit(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при посещении занятия'

    def prepare_generalized_message(self):
        return (
            f'На вашем абонементе:\n'
            f'{self.clientsub.subscription.name}\n'
            f'остаток посещений: {self.clientsub.visits_left}'
        )


class ClientSubscriptionExtend(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при продление абонемента'

    def prepare_generalized_message(self):
        return (
            f'Вам продлили абонемент:\n'
            f'{self.clientsub.subscription.name}\n'
            f'Остаток посещений: {self.clientsub.visits_left}'
        )


class ClientUpdateBalance(Message):

    detailed_description = 'Уведомление при изменении баланса клиента'

    def prepare_generalized_message(self):
        return (
            f'Ваш баланс составляет: {self.recipients[0].balance} ₽'
        )
