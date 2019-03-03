from __future__ import annotations

from typing import List, Union

from crm.models import Client
from bot.api.vkapi import send_message


class Message:

    def __init__(self, client: Union[Client, List[Client]], personalized=False):
        self.personalized = personalized

        if isinstance(client, Client):
            self.clients = [client]
        elif isinstance(client, list):
            # Empty list is valid data, but no message will be sent
            self.clients = client
        else:
            raise ValueError('Invalid client argument passed')

    def send_message(self):
        if not len(self.clients):
            # Early check for empty list, for skip message generation
            return

        try:
            msg = self.prepare_generalized_msg()
        except NotImplementedError:
            msg = ''

        if not len(msg):
            # Don't send any messages, if it was empty
            return

        for client in self.clients:
            if not client.vk_user_id:
                # Skip users without vk
                continue

            if self.personalized:
                msg = self.personalize(msg, client)

            send_message(client.vk_user_id, client.vk_message_token, msg)

    def prepare_generalized_msg(self):
        raise NotImplementedError()

    # noinspection PyMethodMayBeStatic
    def personalize(self, msg: str, client: Client) -> str:
        # Ignore check for empty msg, as at this moment it will be already
        # non empty
        fixed_msg = msg[0].lower() + msg[1:]

        return f'{client.name}, {fixed_msg}'
