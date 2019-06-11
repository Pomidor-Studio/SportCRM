from datetime import (
    date,
    timedelta,
)

from django_multitenant.utils import set_current_tenant

from bot.api.messages import (
    ClientHaveNegativeBalance, UsersToManagerBirthday, UserToUserBirthday,
)
from bot.tasks import notify_clients_about_future_event
from crm.models import Client, Company, INTERNAL_COMPANY, Manager


def receivables():

    for client in Client.objects.filter(balance__lt=0):
        set_current_tenant(client.company)
        ClientHaveNegativeBalance(client, personalized=False).send_message()


def birthday():
    current_date = date.today()
    month = current_date.month
    day = current_date.day

    companies = Company.objects.exclude(display_name=INTERNAL_COMPANY)

    for company in companies:
        set_current_tenant(company)
        clients = Client.objects.filter(
            birthday__month=month, birthday__day=day, company_id=company.id
        )

        # skip, if there no any client with birthday
        if not clients.count():
            continue

        clients_list = list(clients)
        UserToUserBirthday(clients_list, personalized=True).send_message()

        managers = list(Manager.objects.filter(company_id=company.id))
        UsersToManagerBirthday(
            managers, personalized=True, clients=clients_list
        ).send_message()


def future_event():
    tomorrow = date.today() + timedelta(days=1)
    notify_clients_about_future_event(tomorrow)
