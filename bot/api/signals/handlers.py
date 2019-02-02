#Поправить парсер!
from django.db.models.signals import post_save
from django.dispatch import receiver
from crm.models import ClientSubscriptions, Client
from bot.api.settings import *
from bot.api.vkapi import send_message


@receiver(post_save, sender=ClientSubscriptions)
def sub_client(sender, **kwargs):
    client_subscription:ClientSubscriptions = kwargs['instance']

    # id = ''
    # sub_list = ''
    # i = 0
    # j = 0
    # k = {}
    #
    # for sub in sub:
    #     if sub == '0' or sub == '1' or sub == '2' or sub == '3' or sub == '4' or sub == '5' or sub == '6' or sub == '7' or sub == '8' or sub == '9':
    #         id = id + sub
    #         i = 1
    #         continue
    #     if i == '1':
    #         break
    #
    # id = int(id)
    # i = 0
    #
    # subscription = ClientSubscriptions.objects.filter(id=id)
    # for sub in subscription:
    #     client_id = sub.client_id
    #     purchase_date = sub.purchase_date
    #     visits_left = sub.visits_left
    #     subscription = sub.subscription
    #     k[0] = [subscription, visits_left]
    #
    # sub = str(k)
    #
    # client = Client.objects.filter(id=client_id)
    # for cl in client:
    #     name = cl.name
    #     vk_user_id = cl.vk_user_id
    #
    # for sub in sub:
    #     if sub == '{' or sub == '[' or sub == '<' or sub == '}':
    #         continue
    #     if sub == '>':
    #         j = 1
    #         continue
    #     if j == 1 and sub == ',':
    #         sub_list = sub_list + ', Остаток посещений: '
    #         j = 0
    #         continue
    #     if sub == ']':
    #         i = 1
    #         continue
    #     if i == 1:
    #         sub_list = sub_list + '\n'
    #         i = 0
    #         continue
    #     sub_list = sub_list + sub

    message = client_subscription.client.name +'!\n Вы приобрели абонемент:' + client_subscription.subscription.name + \
              '!\n Действующий до :' + str(client_subscription.end_date)

    send_message(client_subscription.client.vk_user_id, token, message, '')
