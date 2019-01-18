import command_system

def info():
   message = 'Список команд:\n'
   for c in command_system.command_list:
        message += c.keys[0] + ' - ' + c.description + '\n'
   return message, ''

info_command = command_system.Command()

info_command.keys = ['помощь', 'помоги', 'help','хелп']
info_command.description = 'Покажу список команд'
info_command.process = info