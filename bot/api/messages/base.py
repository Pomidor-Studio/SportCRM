from __future__ import annotations

from typing import List, Union

from bot.api.vkapi import send_message
from crm.models import Client


class Message:

    detailed_description: str
    _registry = []

    def __init__(self, client: Union[Client, List[Client]], personalized=False):

        self.personalized = personalized

        if isinstance(client, Client):
            self.clients = [client]
        elif isinstance(client, list):
            # Empty list is valid data, but no message will be sent
            self.clients = client
        else:
            raise ValueError('Invalid client argument passed')

    def __init_subclass__(cls, abstract=False, *args, **kwargs) -> None:
        super().__init_subclass__()
        if abstract:
            return

        if not hasattr(cls, 'detailed_description') or \
                cls.detailed_description is None:
            raise ValueError(
                'detailed_description must be set on '
                f'{cls.__module__}.{cls.__qualname__}, '
                'as it will be shown for manager in UI'
            )
        __class__._registry.append(cls)

    def is_enabled_message(self) -> bool:
        return True

    def send_message(self):
        if not self.is_enabled_message():
            return

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
