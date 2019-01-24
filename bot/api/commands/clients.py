from crm.models import Client
from bot.api.command_system import Command

def test():
    a = Client.objects.filter(id = 1)
    message = a
    return message, ''

test_command = Command()

test_command.keys = ['test']
test_command.description = 'test'
test_command.process = test