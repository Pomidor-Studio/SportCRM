import datetime

from bot.api.messages import ClosedEvent
from crm.models import DayOfTheWeekClass, Event, Manager, ClientSubscriptions


def event_closing():
    now = datetime.datetime.now()

    dws = DayOfTheWeekClass.objects.filter(
        day=now.day,
        end_time__range=(
            now.time() - datetime.timedelta(minutes=40),
            now.time() - datetime.timedelta(minutes=30),
        )
    )

    for dw_event in dws:
        qs = Event.objects.filter(
            event_class=dw_event.event,
            date=now.date()
        )
        if qs.exists():
            for event in qs:
                _send_end_notification(event)
                _recalc_clients_visits(event)


def _send_end_notification(event: Event):
    managers = list(Manager.objects.filter(company=event.company))
    ClosedEvent(managers, event=event).send_message()


def _recalc_clients_visits(event: Event):
    for cs in ClientSubscriptions.objects.active_subscriptions_to_event(event):
        nvl = cs.normalized_visits_left
        if cs.visits_left != nvl:
            cs.visits_left = nvl
            cs.save()
