from bot.api.command_system import command_list
from bot.api.command_system import Command

def info():
   message = 'Список команд:\n'
   for c in command_list:
        message += c.keys[0] + ' - ' + c.description + '\n'
   return message, ''

info_command = Command()

info_command.keys = ['помощь', 'помоги', 'help','хелп']
info_command.description = 'Покажу список команд'
info_command.process = info