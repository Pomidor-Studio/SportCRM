from bot.api.command_system import Command

def hello():
   message = 'Привет, друг!\nЯ БОТ, создан для уведомления'
   return message, ''

hello_command = Command()

hello_command.keys = ['привет', 'hello', 'дратути', 'здравствуй', 'здравствуйте', 'hi', 'прив']
hello_command.description = 'Поприветствую тебя'
hello_command.process = hello