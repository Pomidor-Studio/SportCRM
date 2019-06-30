from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Prefetch
from django_multitenant.utils import set_current_tenant

from bot.api import messages
from crm.models import Client, ClientSubscriptions, Event, Manager, EventClass


def notify_event_cancellation(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    clients = list(Client.objects.with_active_subscription_to_event(event))
    messages.CancelledEvent(clients, event=event).send_message()


def notify_client_buy_subscription(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientSubscriptionBuy(
        client_sub.client, personalized=True, clientsub=client_sub
    ).send_message()


def notify_client_subscription_visit(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientSubscriptionVisit(
        client_sub.client, personalized=True, clientsub=client_sub
    ).send_message()


def notify_client_subscription_extend(subscription_id: int):
    try:
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
    except ClientSubscriptions.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientSubscriptionExtend(
        client_sub.client, personalized=True, clientsub=client_sub
    ).send_message()


def notify_client_balance(client_id: int):
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        # Invalid event id passed
        return

    messages.ClientUpdateBalance(client, personalized=True).send_message()


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


def notify_manager_event_closed(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    managers = list(Manager.objects.all())
    messages.ClosedEvent(managers, event=event, personalized=True).send_message()


def notify_manager_event_opened(event_id: int):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        # Invalid event id passed
        return

    managers = list(Manager.objects.all())
    messages.OpenedEvent(managers, event=event, personalized=True).send_message()


def notify_manager_about_signup(event_id: int, client_id: int):
    try:
        event = Event.objects.get(id=event_id)
        client = Client.objects.get(id=client_id)
    except (Event.DoesNotExist, Client.DoesNotExist):
        # Wrong params were passed
        return

    managers = list(Manager.objects.all())
    messages.SignupClient(managers, event=event, client=client).send_message()


def notify_manager_about_unsignup(event_id: int, client_id: int):
    try:
        event = Event.objects.get(id=event_id)
        client = Client.objects.get(id=client_id)
    except (Event.DoesNotExist, Client.DoesNotExist):
        # Wrong params were passed
        return

    managers = list(Manager.objects.all())
    messages.UnsignupClient(managers, event=event, client=client).send_message()


def send_registration_notification(user_id: int, password: str):
    user = get_user_model().objects.get(id=user_id)
    send_mail(
        'Регистрация заявки',
        f'Уважаемый клиент, вы зарегистрировались на сайте '
        f'"Твой спортивный клуб", на пробный месяц использования.\n'
        f'Ваш логин {user.username}\n'
        f'Ваш пароль {password}',
        'yourclubdev@gmail.com',
        [user.email],
        fail_silently=False,
    )
