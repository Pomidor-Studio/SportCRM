import os
from importlib import import_module
from bot.api.command_system import command_list
from bot.api.vkapi import send_message


def damerau_levenshtein_distance(s1, s2):
   d = {}
   lenstr1 = len(s1)
   lenstr2 = len(s2)
   for i in range(-1, lenstr1 + 1):
       d[(i, -1)] = i + 1
   for j in range(-1, lenstr2 + 1):
       d[(-1, j)] = j + 1
   for i in range(lenstr1):
       for j in range(lenstr2):
           if s1[i] == s2[j]:
               cost = 0
           else:
               cost = 1
           d[(i, j)] = min(
               d[(i - 1, j)] + 1,  # deletion
               d[(i, j - 1)] + 1,  # insertion
               d[(i - 1, j - 1)] + cost,  # substitution
           )
           if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
               d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)  # transposition
   return d[lenstr1 - 1, lenstr2 - 1]


def load_modules():
   # путь от рабочей директории, ее можно изменить в настройках приложения
   files = os.listdir("bot/api/commands")
   modules = list(filter(lambda x: x.endswith('.py'), files))
   for m in modules:
       j = 'bot.api.commands.' + m[0:-3]
       import_module(j)


def get_answer(body, user_id):
   message = "Прости, не понимаю тебя. Напиши 'помощь', чтобы узнать мои команды"
   attachment = ''
   distance = len(body)
   command = None
   key = ''
   for c in command_list:
       for k in c.keys:
           d = damerau_levenshtein_distance(body, k)
           if d < distance:
               distance = d
               command = c
               key = k
               if distance == 0:
                   message, attachment = c.process(user_id)
                   return message, attachment
   if distance < len(body)*0.4:
       message, attachment = command.process(user_id)
       message = 'Я понял ваш запрос как "%s"\n\n' % key + message
   return message, attachment


def create_answer(data, token):
    load_modules()
    user_id = data['user_id']
    message, attachment = get_answer(data['body'].lower(), user_id)
    send_message(user_id, token, message, attachment)
