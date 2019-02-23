from typing import Tuple, Optional
from .base import Command
from crm.models import Client, SubscriptionsType
from datetime import date, timedelta


class Schedule_clients(Command):
    keys = ['расписание']
    description = 'Информация о Вашем расписание'

    def process(self, user_id: int) -> Tuple[str, Optional[str]]:

        messages = []
        start_date = date.today()
        end_date = start_date + timedelta(14)

        client = Client.objects.filter(vk_user_id=user_id)
        check_cl = client.count()

        if not check_cl:
            messages.append('Вас нет в базе!')
            return ''.join(messages), ''

        if check_cl > 1:
            messages.append('На ваш аккаунт зарегистрировано несколько учеников!\n')

        for cl in client:
            messages.append('\n')
            name = cl.name

            messages.extend([name, '!\n'])

            subscriptions = cl.clientsubscriptions_set.filter(
                end_date__gte=start_date,
                visits_left__gt=0)
            check_sub = subscriptions.exists()

            if not check_sub and check_cl == 1:
                messages = [name, '!\nВы еще не приобрели абонемент!']
                continue
            elif not check_sub:
                messages.append('\nВы еще не приобрели абонемент!\n')
                continue

            for sub in subscriptions:
                sub_type = SubscriptionsType.objects.get(id=sub.subscription_id)
                events = sub_type.event_class.filter()

                for ev in events:
                    messages.append('\n')
                    calendar = ev.get_calendar(start_date, end_date)
                    for key, value in calendar.items():
                        messages.extend([str(value), '\n'])

        return ''.join(messages), ''
