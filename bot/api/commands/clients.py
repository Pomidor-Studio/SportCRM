from crm.models import Client
from bot.api.command_system import Command
from datetime import datetime, timezone


def get_info_subscription(user_id):

    message = ''
    current_date = datetime.now(timezone.utc)

    vk_user_id = user_id

    client = Client.objects.filter(vk_user_id=vk_user_id)
    check_cl = client.count()

    if check_cl == 0:
        message = 'Вас нет в базе!'
        return message, ''

    if check_cl > 1:
        message = 'На ваш аккаунт зарегистрировано несколько учеников!\n'

    for cl in client:
        i = 0
        message = message + '\n'
        name = cl.name
        balance = cl.balance

        if balance != 0:
            message = message + name + '!\nВаш баланс: ' + str(balance) + '\nИнформация о ваших абонементах:\n'
        else:
            message = message + name + '!\nИнформация о ваших абонементах:\n'

        subscription = cl.clientsubscriptions_set.filter(end_date__gte=current_date, visits_left__gt=0)
        check_sub = subscription.exists()

        if check_sub == 0 and check_cl == 1:
            message = name + '!\nВы еще не приобрели абонемент!'
            return message, ''
        elif check_sub == 0:
            message = message + '\nВы еще не приобрели абонемент!\n'

        for sub in subscription:
            subscription = sub.subscription.name
            visits_left = sub.visits_left
            end_date = '{:%d-%m-%Y}'.format(sub.end_date)
            message = message + str(i+1) + ') ' + subscription + '\nОстаток посещений: ' + str(visits_left) + \
                '\nДействующий до: ' + end_date + '\n'
            i += 1

    return message, ''


clients_command = Command()

clients_command.keys = ['абонементы', 'мои абонементы', 'информация о моих абонементах']
clients_command.description = 'Информация о Ваших абонементах'
clients_command.process = get_info_subscription
