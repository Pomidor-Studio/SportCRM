#Сделать условие, Если НЕТ клиента в базе;
#Сделать нормальный парсе списка;
#Косяк с ботом, юзер айди тащит не правильный;

from crm.models import Client, ClientSubscriptions
from bot.api.command_system import Command
from bot.api.messageHandler import data1



def get_info_abonements():
    vk_user_id = int(data1)

    client = Client.objects.filter(vk_user_id=vk_user_id)

    k = {}
    sub_list = ''
    i = 0

    for cl in client:
        id = cl.id
        name = cl.name

    subscription = ClientSubscriptions.objects.filter(client_id=id)

    for sub in subscription:
        subscription = sub.subscription
        visits_left = sub.visits_left
        k[i] = [subscription, visits_left]
        i += 1

    sub = str(k)
    i = 0
    j = 0

    for sub in sub:
        if sub == '{' or sub == '[' or sub == '<' or sub == '}':
            continue
        if sub == '>':
            j = 1
            continue
        if j == 1 and sub == ',':
            sub_list = sub_list + ', Остаток посещений: '
            j = 0
            continue
        if sub == ']':
            i = 1
            continue
        if i == 1:
            sub_list = sub_list + '\n'
            i = 0
            continue
        sub_list = sub_list + sub

    message = str(name + '!\n Информация о ваших абонементах:' + '\n' + sub_list)
    return message, ''


test_command = Command()

test_command.keys = ['информация', 'абонементы', 'мои абонементы', 'информация о моих абонементах']
test_command.description = 'Информация о Ваших абонементах'
test_command.process = get_info_abonements