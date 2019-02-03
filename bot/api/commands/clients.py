from crm.models import Client, ClientSubscriptions
from bot.api.command_system import Command


def get_info_abonements(user_id):

    vk_user_id = user_id

    client = Client.objects.filter(vk_user_id=vk_user_id)

    proverka = str(client)
    proverka_len = len(proverka)
    if proverka_len == 13:
        message = 'Вас нет в базе!'
        return message, ''

    i = 0
    for cl in client:
        id = cl.id
        name = cl.name
    message = str(name) + '!\nИнформация о ваших абонементах:\n'

    subscription = ClientSubscriptions.objects.filter(client_id=id)

    proverka = str(subscription)
    proverka_len = len(proverka)
    if proverka_len == 13:
        message = name + '!\nВы еще не приобрели абонемент!'
        return message, ''

    for sub in subscription:
        subscription = sub.subscription.name
        visits_left = sub.visits_left
        end_date = str(sub.end_date)
        end_date = end_date[0: -15]
        message = message + (i+1) + ') ' + subscription + '\nОстаток посещений: ' + str(visits_left) + \
            '\n Действующий до: ' + end_date + '\n'
        i += 1

    return message, ''


test_command = Command()

test_command.keys = ['абонементы', 'мои абонементы', 'информация о моих абонементах']
test_command.description = 'Информация о Ваших абонементах'
test_command.process = get_info_abonements
