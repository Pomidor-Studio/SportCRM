#Поправить парсер!
from django.db.models.signals import post_save
from django.dispatch import receiver
from crm.models import ClientSubscriptions
from bot.api.settings import *
from bot.api.vkapi import send_message


@receiver(post_save, sender=ClientSubscriptions)
def sub_client(sender, **kwargs):
    client_subscription:ClientSubscriptions = kwargs['instance']

    end_date = str(client_subscription.end_date)
    end_date = end_date[0: -15]

    message = client_subscription.client.name +'!\nВы приобрели абонемент:\n ' + client_subscription.subscription.name + \
              '!\nДействующий до:\n ' + str(end_date)

    send_message(client_subscription.client.vk_user_id, token, message, '')
