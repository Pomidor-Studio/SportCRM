from typing import Tuple, Optional
from .base import Command
from crm.models import Client
from datetime import datetime, timezone


class Clients(Command):
    keys = ['абонементы', 'мои абонементы', 'информация о моих абонементах']
    description = 'Информация о Ваших абонементах'

    def process(self, user_id: int) -> Tuple[str, Optional[str]]:

        messages = []
        current_date = datetime.now(timezone.utc)

        vk_user_id = user_id

        client = Client.objects.filter(vk_user_id=vk_user_id)
        check_cl = client.count()

        if not check_cl:
            messages.append('Вас нет в базе!')
            return ''.join(messages), ''

        if check_cl > 1:
            messages.append('На ваш аккаунт зарегистрировано несколько учеников!\n')

        for cl in client:
            messages.append('\n')
            name = cl.name
            balance = cl.balance

            messages.extend([name, '!\n'])
            if balance:
                messages.extend(['Ваш баланс: ', str(balance), '\n'])

            messages.append('Информация о ваших абонементах:\n')

            subscriptions = cl.clientsubscriptions_set.filter(
                end_date__gte=current_date,
                visits_left__gt=0).select_related('subscription')
            check_sub = subscriptions.exists()

            if not check_sub and check_cl == 1:
                messages = [name, '!\nВы еще не приобрели абонемент!']
            elif not check_sub:
                messages.append('\nВы еще не приобрели абонемент!\n')

            for idx, sub in enumerate(subscriptions, start=1):
                messages.extend([
                    str(idx), ') ', sub.subscription.name,
                    '\nОстаток посещений: ', str(sub.visits_left),
                    '\nДействующий по: ',
                    '{:%d.%m.%Y}'.format(sub.end_date), '\n'
                ])

        return ''.join(messages), ''

