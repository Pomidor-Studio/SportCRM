from datetime import (
    date,
    timedelta,
)

from bot.api.messages import (
    ClientHaveNegativeBalance, UsersToManagerBirthday, UserToUserBirthday, FutureEvent,
)
from bot.tasks import notify_clients_about_future_event
from crm.models import Client, Company, INTERNAL_COMPANY, Manager, EventClass


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
    notify_clients_about_future_event(tomorrow)
