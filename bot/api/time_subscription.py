'''
from crm.models import ClientSubscriptions
from bot.api.settings import *
from bot.api.vkapi import send_message
from datetime import datetime, timedelta, timezone


def time_sub():
    subscription = ClientSubscriptions.objects.all()

    current_date = datetime.now(timezone.utc)

    for sub in subscription:
        subscription = sub.subscription.name

        end_date = sub.end_date
        delta = end_date - current_date

        vk_user_id = sub.client.vk_user_id
        name = sub.client.name

        if delta.days == 1:
            message = name + '!\nЧерез 1 день закончится ваш абонемент: \n' + subscription
            send_message(vk_user_id, token, message, '')
    return
'''