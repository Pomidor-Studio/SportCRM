import datetime

import pendulum
from django_multitenant.utils import set_current_tenant

from bot.api.messages import ClosedEvent
from crm.models import DayOfTheWeekClass, Event, Manager, ClientSubscriptions

DIFF_START = datetime.timedelta(minutes=39, seconds=59)
DIFF_END = datetime.timedelta(minutes=30)


def event_closing():
    p_now: pendulum.DateTime = pendulum.DateTime.now()
    p_start = p_now - DIFF_START
    day_to_check = p_start.weekday()

    dws = DayOfTheWeekClass.objects.filter(
        day=day_to_check,
        end_time__range=(
            p_start.time(),
            (p_now - DIFF_END).time()
        )
    )

    for dw_event in dws:
        set_current_tenant(dw_event.company)
        qs = Event.objects.filter(
            event_class=dw_event.event,
            date=p_start.date()
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
