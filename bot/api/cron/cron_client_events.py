from datetime import (
    date,
    timedelta,
)

from bot.api.messages import (
    ClientHaveNegativeBalance, UsersToManagerBirthday, UserToUserBirthday, FutureEvent,
)
from bot.tasks import notify_clients_about_future_event
from crm.models import Client, Company, INTERNAL_COMPANY, Manager, Event, ClientSubscriptions


def receivables():

    for client in Client.objects.filter(balance__lt=0):
        ClientHaveNegativeBalance(client, personalized=False).send_message()


def birthday():
    current_date = date.today()
    month = current_date.month
    day = current_date.day

    companies = Company.objects.exclude(display_name=INTERNAL_COMPANY)

    for company in companies:
        clients = Client.objects.filter(
            birthday__month=month, birthday__day=day, company_id=company.id)

        # skip, if there no any client with birthday
        if not clients.count():
            continue

        clients_list = list(clients)
        UserToUserBirthday(clients_list, personalized=True).send_message()

        managers = list(Manager.objects.filter(company_id=company.id))
        UsersToManagerBirthday(
            managers, personalized=True, clients=clients_list
        ).send_bulk_message()


def future_event():
    tomorrow = date.today() + timedelta(days=1)

    cs = ClientSubscriptions.objects.active_subscriptions_to_date(tomorrow).values_list(
        'subscription__event_class', 'company', 'subscription__event_class__event__date'
    ).filter(
        subscription__event_class__event__isnull=True,
    ).all()

    events = []
    for event_class_id, company_id, event_date in cs:
        # TODO: можно будет отказать в Django 2.2
        # https://docs.djangoproject.com/en/2.2/ref/models/querysets/#bulk-create
        if event_date:
            continue
        events.append(
            Event(
                date=tomorrow,
                event_class_id=event_class_id,
                company_id=company_id,
            )
        )

    Event.objects.bulk_create(
        events,
        batch_size=100,
    )

    tomorrow_event_ids = Event.objects.filter(
        date=tomorrow,
        canceled_at__isnull=True,
    ).values_list('id', flat=True)

    for event_id in tomorrow_event_ids:
        notify_clients_about_future_event(event_id)
