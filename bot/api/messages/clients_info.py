from bot.api.messages.base import Message
from crm.models import ClientSubscriptions, Client


class ClientSubscriptionBuy(Message):

    def __init__(self, client, personalized=False, *, clientsub: ClientSubscriptions):
        self.clientsub = clientsub

        super().__init__(client, personalized)

    def prepare_generalized_msg(self):
        return (
            f'{self.clientsub.client.name} !\nВы приобрели абонемент:\n'
            f'{self.clientsub.subscription.name} !\nДействующий до:\n{self.clientsub.end_date:%d.%m.%Y}'
        )


class ClientSubscriptionVisit(Message):

    def __init__(self, client, personalized=False, *, clientsub: ClientSubscriptions):
        self.clientsub = clientsub

        super().__init__(client, personalized)

    def prepare_generalized_msg(self):
        return (
            f'{self.clientsub.client.name} !\nНа вашем абонементе:\n'
            f'{self.clientsub.subscription.name}\nОстаток посещений: {self.clientsub.visits_left}'
        )


class ClientSubscriptionExtend(Message):

    def __init__(self, client, personalized=False, *, clientsub: ClientSubscriptions):
        self.clientsub = clientsub

        super().__init__(client, personalized)

    def prepare_generalized_msg(self):
        return (
            f'{self.clientsub.client.name} !\nВам продлили абонемент:\n'
            f'{self.clientsub.subscription.name}\nОстаток посещений: {self.clientsub.visits_left}'
        )


class ClientUpdateBalance(Message):

    def __init__(self, client, personalized=False, *, thisclient: Client):
        self.thisclient = thisclient

        super().__init__(client, personalized)

    def prepare_generalized_msg(self):
        return (
            f'{self.thisclient.name}!\nВаш баланс составляет: {self.thisclient.balance} ₽'
        )
