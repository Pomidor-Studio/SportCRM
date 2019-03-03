from sportcrm import celery_app

from crm.models import Event, ClientSubscriptions, Client
from bot.api.messages.event import CancelledEvent


@celery_app.task
def notify_event_cancellation(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    clients = list(Client.objects.with_active_subscription_to_event(event))
    CancelledEvent(clients, event=event).send_message()

