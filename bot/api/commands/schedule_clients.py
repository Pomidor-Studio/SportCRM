from bot.api.command_system import Command
from crm.models import Client, SubscriptionsType
from datetime import datetime, timezone
#

def get_info_schedule(user_id):

    messages = []
    current_date = datetime.now(timezone.utc)

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
            end_date__gte=current_date,
            visits_left__gt=0)
        check_sub = subscriptions.exists()

        if not check_sub and check_cl == 1:
            messages = [name, '!\nВы еще не приобрели абонемент!']
            continue
        elif not check_sub:
            messages.append('\nВы еще не приобрели абонемент!\n')
            continue

        for sub in subscriptions:
            subb = SubscriptionsType.objects.filter(id=sub.subscription_id)

            for sub in subb:
                events = sub.event_class.filter()
                messages = str(events)

    return ''.join(messages), ''


schedule_command = Command()

schedule_command.keys = ['расписание']
schedule_command.description = 'Информация о Вашем расписание'
schedule_command.process = get_info_schedule
