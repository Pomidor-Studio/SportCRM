from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Prefetch
from django_multitenant.utils import set_current_tenant

from bot.api import messages
from crm.models import Client, ClientSubscriptions, Event, Manager, EventClass

from sportcrm.celery import app

@app.task
def notify_event_cancellation(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    clients = list(Client.objects.with_active_subscription_to_event(event))
    messages.CancelledEvent(clients, event=event).send_message()


@app.task
def notify_client_buy_subscription(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientSubscriptionBuy(
        client_sub.client, personalized=True, clientsub=client_sub
    ).send_message()


@app.task
def notify_client_subscription_visit(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientSubscriptionVisit(
        client_sub.client, personalized=True, clientsub=client_sub
    ).send_message()


@app.task
def notify_client_subscription_extend(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientSubscriptionExtend(
        client_sub.client, personalized=True, clientsub=client_sub
    ).send_message()


@app.task
def notify_client_balance(client_id: int):
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientUpdateBalance(client, personalized=True).send_message()


@app.task
def notify_clients_about_future_event(dt):
    event_classes = EventClass.objects.in_range(
        dt, dt
    ).filter(
        dayoftheweekclass__day=dt.weekday(),
        subscriptionstype__one_time=False
    ).prefetch_related(
        Prefetch(
            'event_set',
            Event.objects.filter(date=dt, attendance__signed_up=True, attendance__marked=False)
        )
    ).distinct().all()
    cs = ClientSubscriptions.objects.active_subscriptions_to_date(dt)

    for event_class in event_classes:
        set_current_tenant(event_class.company)
        client_ids = cs.filter(
            subscription__event_class=event_class,
            visits_left__gt=1
        ).values_list('client', flat=True).all()
        client_ids = set(client_ids)

        last_visit_client_ids = cs.filter(
            subscription__event_class=event_class,
            visits_left=1
        ).values_list('client', flat=True).all()
        last_visit_client_ids = set(last_visit_client_ids)

        for event in event_class.event_set.all():
            clients = event.attendance_set.filter(
                marked=False, signed_up=True
            ).values_list('client', flat=True)
            client_ids |= set(clients)
        client_ids -= last_visit_client_ids

        clients = list(Client.objects.filter(id__in=client_ids).all())
        last_visit_clients = list(Client.objects.filter(id__in=last_visit_client_ids).all())

        if clients:
            messages.FutureEvent(clients, date=dt, event_class=event_class).send_message()
        if last_visit_clients:
            messages.LastFutureEvent(last_visit_clients, date=dt, event_class=event_class).send_message()


@app.task
def notify_manager_event_closed(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    managers = list(Manager.objects.all())
    messages.ClosedEvent(managers, event=event, personalized=True).send_message()


@app.task
def notify_manager_event_opened(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    managers = list(Manager.objects.all())
    messages.OpenedEvent(managers, event=event, personalized=True).send_message()


@app.task
def notify_manager_about_signup(event_id: int, client_id: int):
    try:
        event = Event.objects.get(id=event_id)
        client = Client.objects.get(id=client_id)
    except (Event.DoesNotExist, Client.DoesNotExist):
        # Wrong params were passed
        return

    managers = list(Manager.objects.all())
    messages.SignupClient(managers, event=event, client=client).send_message()


@app.task
def notify_manager_about_unsignup(event_id: int, client_id: int):
    try:
        event = Event.objects.get(id=event_id)
        client = Client.objects.get(id=client_id)
    except (Event.DoesNotExist, Client.DoesNotExist):
        # Wrong params were passed
        return

    managers = list(Manager.objects.all())
    messages.UnsignupClient(managers, event=event, client=client).send_message()


@app.task
def send_registration_notification(user_id: int, password: str):

    user = get_user_model().objects.get(id=user_id)

    msg_plain = render_to_string('bot/email/registration_notification.txt',
                                 {'user': user, 'password': password})

    msg_html = render_to_string('bot/email/registration_notification.html',
                                {'user': user, 'password': password})

    send_mail(
        'Регистрация заявки',
        msg_plain,
        settings.MAIL_FROM,
        [user.email],
        html_message=msg_html,
        fail_silently=False,
    )


@app.task
def send_registration_notification_manager(user_id: int):

    user = get_user_model().objects.get(id=user_id)
    company = user.company
    manager = user.manager

    msg_plain = render_to_string('bot/email/registration_notification_manager.txt',
                                 {'user': user, 'manager': manager, 'company': company})

    msg_html = render_to_string('bot/email/registration_notification_manager.html',
                                {'user': user, 'manager': manager, 'company': company})

    send_mail(
        'Регистрация заявки ' + company.name,
        msg_plain,
        settings.MAIL_FROM,
        [settings.MAIL_MANAGER],
        html_message=msg_html,
        fail_silently=False,
    )

