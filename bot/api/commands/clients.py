from crm.models import Client, ClientSubscriptions
from bot.api.command_system import Command


def get_info_subscription(user_id):

    vk_user_id = user_id

    check = Client.objects.filter(vk_user_id=vk_user_id).exists()

    if check == 0:
        message = 'Вас нет в базе!'
        return message, ''

    client = Client.objects.get(vk_user_id=vk_user_id)

    i = 0

    id = client.id
    name = client.name
    message = name + '!\nИнформация о ваших абонементах:\n'

    subscription = ClientSubscriptions.objects.filter(client_id=id)
    check = ClientSubscriptions.objects.filter(client_id=id).exists()

    if check == 0:
        message = name + '!\nВы еще не приобрели абонемент!'
        return message, ''

    for sub in subscription:
        subscription = sub.subscription.name
        visits_left = sub.visits_left
        end_date = '{:%d-%m-%Y}'.format(sub.end_date)
        message = message + str(i+1) + ') ' + subscription + '\nОстаток посещений: ' + str(visits_left) + '\n Действующий до: ' + end_date + '\n'
        i += 1

    return message, ''


clients_command = Command()

clients_command.keys = ['абонементы', 'мои абонементы', 'информация о моих абонементах']
clients_command.description = 'Информация о Ваших абонементах'
clients_command.process = get_info_subscription
