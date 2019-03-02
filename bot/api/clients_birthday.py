from crm.models import Client, Company, Manager
from bot.api.settings import *
from bot.api.vkapi import send_message
from datetime import date


def birthday():
    current_date = date.today()
    month = current_date.month
    day = current_date.day

    companies = Company.objects.filter()

    for company in companies:
        message_managers = []
        message_managers.append('Сегодня День рождение:\n')

        clients = Client.objects.filter(birthday__month=month,
                                        birthday__day=day,
                                        company_id=company.id)

        for cl in clients:
            message = []
            message_managers.extend([cl.name, '(vk.com/id', str(cl.vk_user_id), ')\n'])
            message.extend([cl.name, '!\n'])
            message.append('Поздравляем вас с Днем рождения!')
            send_message(cl.vk_user_id, token, ''.join(message), '')

        managers = Manager.objects.filter(company_id=company.id)

        for manager in managers:
            send_message(manager.user.vk_id, token, ''.join(message_managers), '')

    return
