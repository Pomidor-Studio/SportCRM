from django.db.models.signals import post_save
from django.dispatch import receiver
from crm.models import ClientSubscriptions
from bot.api.vkapi import send_message


@receiver(post_save, sender=ClientSubscriptions)
def sub_client(sender, created, **kwargs):
    client_subscription: ClientSubscriptions = kwargs['instance']

    vk_user_id = client_subscription.client.vk_user_id
    token = client_subscription.client.vk_message_token
    message = []

    if vk_user_id is None:
        return

    if created is True:
        end_date = '{:%d-%m-%Y}'.format(client_subscription.end_date)

        message.extend([client_subscription.client.name, '!\nВы приобрели абонемент:\n ',
                        client_subscription.subscription.name, '!\nДействующий до:\n', end_date])
        message = ''.join(message)

        send_message(vk_user_id, token, message, '')

    else:
        visits_left = client_subscription.visits_left

        if visits_left == 1:
            message.extend([client_subscription.client.name, '!\nНа вашем абонементе:\n',
                            client_subscription.subscription.name, '\nОсталось 1 посещение!'])
            message = ''.join(message)

            send_message(vk_user_id, token, message, '')
        return
