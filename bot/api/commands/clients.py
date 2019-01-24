from crm.models import SubscriptionsType
from bot.api.command_system import Command

def test():
    a = SubscriptionsType.objects.filter(id = 1)
    message = str(a)
    return message, ''

test_command = Command()

test_command.keys = ['test']
test_command.description = 'test'
test_command.process = test