from typing import Tuple, Optional
from bot.api.commands import allowed_commands
from bot.api.commands.base import InvalidCommand
from bot.api.vkapi import send_message


def get_answer(body, user_id):
    message = ""
    attachment = ''
    for command in allowed_commands:
        try:
            msg, attach = command.handle_user_message(body, user_id)
            return msg, attach
        except InvalidCommand:
            pass
    return message, attachment


def create_answer(data, token):
    user_id = data['from_id']
    message, attachment = get_answer(data['text'].lower(), user_id)
    send_message(user_id, token, message, attachment)
