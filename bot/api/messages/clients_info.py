from bot.api.messages.base import Message
from crm.models import ClientSubscriptions, Client


class ClientSubscriptionMessage(Message):

    def __init__(self, client, personalized=True, *, clientsub: ClientSubscriptions):
        self.clientsub = clientsub

        super().__init__(client, personalized)


class ClientSubscriptionBuy(ClientSubscriptionMessage):

    def prepare_generalized_msg(self):
        return (
            f'\nВы приобрели абонемент:\n'
            f'{self.clientsub.subscription.name} !\nДействующий до:\n{self.clientsub.end_date:%d.%m.%Y}'
        )


class ClientSubscriptionVisit(ClientSubscriptionMessage):

    def prepare_generalized_msg(self):
        return (
            f'\nНа вашем абонементе:\n'
            f'{self.clientsub.subscription.name}\nОстаток посещений: {self.clientsub.visits_left}'
        )


class ClientSubscriptionExtend(ClientSubscriptionMessage):

    def prepare_generalized_msg(self):
        return (
            f'\nВам продлили абонемент:\n'
            f'{self.clientsub.subscription.name}\nОстаток посещений: {self.clientsub.visits_left}'
        )


class ClientUpdateBalance(Message):

    def prepare_generalized_msg(self):
        return (
            f'{self.clients[0].name}!\nВаш баланс составляет: {self.clients[0].balance} ₽'
        )
