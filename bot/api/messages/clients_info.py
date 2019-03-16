from bot.api.messages.base import Message
from crm.models import ClientSubscriptions


class ClientSubscriptionMessage(Message, abstract=True):

    def __init__(self, client, personalized=True, *, clientsub: ClientSubscriptions):
        self.clientsub = clientsub

        super().__init__(client, personalized)


class ClientSubscriptionBuy(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при покупке абонемента'

    def prepare_generalized_msg(self):
        return (
            f'\nВы приобрели абонемент:\n'
            f'{self.clientsub.subscription.name} !\nДействующий до:\n{self.clientsub.end_date:%d.%m.%Y}'
        )


class ClientSubscriptionVisit(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при посещении занятия'

    def prepare_generalized_msg(self):
        return (
            f'\nНа вашем абонементе:\n'
            f'{self.clientsub.subscription.name}\nОстаток посещений: {self.clientsub.visits_left}'
        )


class ClientSubscriptionExtend(ClientSubscriptionMessage):

    detailed_description = 'Уведомление при продление абонемента'

    def prepare_generalized_msg(self):
        return (
            f'\nВам продлили абонемент:\n'
            f'{self.clientsub.subscription.name}\nОстаток посещений: {self.clientsub.visits_left}'
        )


class ClientUpdateBalance(Message):

    detailed_description = 'Уведомление при изменении баланса клиента'

    def prepare_generalized_msg(self):
        return (
            f'{self.clients[0].name}!\nВаш баланс составляет: {self.clients[0].balance} ₽'
        )
