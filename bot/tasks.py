from crm.models import Event, ClientSubscriptions, Client
from bot.api.messages.event import CancelledEvent
from bot.api.messages.clients_info import client_subscriptions_buy, client_subscriptions_visits, client_update_balance


def notify_event_cancellation(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    clients = list(Client.objects.with_active_subscription_to_event(event))
    CancelledEvent(clients, event=event).send_message()


def notify_client_buy_subscription(client_id: int):
    try:
        client_sub = ClientSubscriptions.objects.filter(client_id=client_id).latest('id')
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    client_subscriptions_buy(client_sub)


def notify_client_subscription_visit(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    client_subscriptions_visits(client_sub)


def notify_client_balance(client_id: int):
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        # Invalid event id passed
        return

    client_update_balance(client)
