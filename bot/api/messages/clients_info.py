from crm.models import ClientSubscriptions
from bot.api.vkapi import send_message


def client_subscriptions_buy(client_subscription):

    vk_user_id = client_subscription.client.vk_user_id
    token = client_subscription.client.vk_message_token
    message = []

    if vk_user_id is None:
        return

    end_date = '{:%d-%m-%Y}'.format(client_subscription.end_date)

    message.extend([client_subscription.client.name, '!\nВы приобрели абонемент:\n',
                    client_subscription.subscription.name, '!\nДействующий до:\n', end_date])
    message = ''.join(message)

    send_message(vk_user_id, token, message, '')
    return


def client_subscriptions_visits(client_subscription):

    vk_user_id = client_subscription.client.vk_user_id
    token = client_subscription.client.vk_message_token
    message = []

    if vk_user_id is None:
        return

    message.extend([client_subscription.client.name, '!\nНа вашем абонементе:\n',
                    client_subscription.subscription.name, '\nОстаток посещений: ',
                    str(client_subscription.visits_left)])
    message = ''.join(message)

    send_message(vk_user_id, token, message, '')

    return


def client_update_balance(client):

    vk_user_id = client.vk_user_id
    token = client.vk_message_token
    balance = client.balance
    message = []

    if vk_user_id is None:
        return

    message.extend([client.name, '!\nВаш баланс состовляет: ', str(balance)])
    message = ''.join(message)

    send_message(vk_user_id, token, message, '')

    return
