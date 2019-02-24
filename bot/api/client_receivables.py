from crm.models import Client
from bot.api.settings import *
from bot.api.vkapi import send_message


def receivables():

    client = Client.objects.filter(balance__lt=0)
    message = []

    for cl in client:
        name = cl.name
        balance = cl.balance
        message.extend([name, '!\nУ вас есть задолженность!\nСостояние вашего счета: ', str(balance)])
        send_message(token, cl.vk_user_id, ''.join(message), '')

    return
