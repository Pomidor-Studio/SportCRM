from crm.models import Client, Company, Manager
from bot.api.settings import *
from bot.api.vkapi import send_message
from datetime import date


def birthday():
    current_date = date.today()
    month = current_date.month
    day = current_date.day

    company = Company.objects.filter()

    for comp in company:
        message_manage = []
        message_manage.append('Сегодня День рождение:\n')

        clients = Client.objects.filter(birthday__month=month,
                                        birthday__day=day,
                                        company_id=comp.id)

        for cl in clients:
            message = []
            message_manage.extend([cl.name, '(vk.com/id', str(cl.vk_user_id), ')\n'])
            message.extend([cl.name, '!\n'])
            message.append('Поздравляем вас с Днем рождения!')
            send_message(cl.vk_user_id, token, ''.join(message), '')

        manage = Manager.objects.filter(company_id=comp.id)

        for manage in manage:
            send_message(manage.user.vk_id, token, ''.join(message_manage), '')

    return
