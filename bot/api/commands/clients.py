from crm.models import SubscriptionsType, Client, ClientSubscriptions
from bot.api.command_system import Command

id_client = 1

def test():
    a = SubscriptionsType.objects.filter(id = id_client)
    b = Client.objects.filter(id = id_client)
    c = ClientSubscriptions.objects.filter(client_id = id_client)
    k = {}
    kk = {}
    i = 0
    for cl in b:
        name = cl.name
        k[i] = [name]
        i += 1
    for sub in a:
        name = sub.name
        k[i] = [name]
        i += 1
    for sub in c:
        purchase_date = sub.purchase_date
        k[i] = [purchase_date]
        i += 1
    kk[0] = [k]
    message = str(kk[0])
    return message, ''

test_command = Command()

test_command.keys = ['test']
test_command.description = 'test'
test_command.process = test