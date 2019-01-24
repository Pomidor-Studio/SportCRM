from crm.models import SubscriptionsType
from bot.api.command_system import Command

def test():
    a = SubscriptionsType.objects.filter(id = 1)
    k = {}
    i = 0
    for sub in a:
        c = sub.name
        b = sub.price
        d = sub.duration
        j = sub.visit_limit
        k[i] = [c, b, d, j]
        i += 1
    message = str(k[0])
    return message, ''

test_command = Command()

test_command.keys = ['test']
test_command.description = 'test'
test_command.process = test