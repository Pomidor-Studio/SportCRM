from crm.models import Event, ClientSubscriptions, Client, Manager
from bot.api.messages.event import CancelledEvent, ClosedEvent, OpenedEvent
from bot.api.messages.clients_info import ClientSubscriptionBuy, ClientSubscriptionVisit, ClientUpdateBalance, ClientSubscriptionExtend


def notify_event_cancellation(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    clients = list(Client.objects.with_active_subscription_to_event(event))
    CancelledEvent(clients, event=event).send_message()


def notify_client_buy_subscription(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    ClientSubscriptionBuy(client_sub.client, clientsub=client_sub).send_message()


def notify_client_subscription_visit(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    ClientSubscriptionVisit(client_sub.client, clientsub=client_sub).send_message()


def notify_client_subscription_extend(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    ClientSubscriptionExtend(client_sub.client, clientsub=client_sub).send_message()


def notify_client_balance(client_id: int):
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        # Invalid event id passed
        return

    ClientUpdateBalance(client).send_message()


def notify_manager_event_closed(event_id: int, company_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Client.DoesNotExist:
        # Invalid event id passed
        return

    managers = list(Manager.objects.filter(company_id=company_id))
    ClosedEvent(managers, event=event).send_message()


def notify_manager_event_opened(event_id: int, company_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Client.DoesNotExist:
        # Invalid event id passed
        return

    managers = list(Manager.objects.filter(company_id=company_id))
    OpenedEvent(managers, event=event).send_message()
