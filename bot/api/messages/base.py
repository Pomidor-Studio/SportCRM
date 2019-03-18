from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Union
from uuid import UUID, uuid5

from django.template import Context, Template

from bot.api.vkapi import send_bulk_message, send_message
from bot.const import SPORTCRM_NAMESPACE
from bot.models import MessageMeta
from crm.models import Client, Coach, Manager

Recipient = Union[Client, Manager, Coach]


def is_valid_recipient(recipient: Any) -> bool:
    return isinstance(recipient, (Client, Manager, Coach))


@dataclass
class TemplateItem:
    text: str
    example: Any


class Message:

    # Human readable detailed description of message.
    # Will be provided for client in UI part.
    detailed_description: str
    # Default message template, if user won't create any custom template
    default_template: str
    # Describe all allowed template items, for one message
    # This items will be populated in template rendering
    template_args: Dict[str, str] = {}

    _registry = []
    message: str = None

    def __init__(
        self,
        recipient: Union[Recipient, Sequence[Recipient]],
        personalized=False
    ):

        self.personalized = personalized

        # Use direct check of instance as typing provides *static* check
        # and usage of Recipient.__args__ can be dangerous. As this function
        # isn't documented.
        if is_valid_recipient(recipient):
            self.recipients = [recipient]
        elif isinstance(recipient, Sequence):
            # Filter iterable, to skip non-valid recipient items
            # Empty list is valid data, but no message will be sent
            self.recipients = list(filter(is_valid_recipient, recipient))
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
        if not hasattr(cls, 'default_template') or \
                cls.default_template is None:
            raise ValueError(
                'default_template must be set on '
                f'{cls.__module__}.{cls.__qualname__}, '
                'as it will be shown for manager in UI'
            )
        __class__._registry.append(cls)

    @classmethod
    def __full_qualname__(cls) -> str:
        return f'{cls.__module__}.{cls.__qualname__}'

    @classmethod
    def uuid(cls) -> UUID:
        return uuid5(SPORTCRM_NAMESPACE, cls.__full_qualname__())

    @classmethod
    def is_enabled_message(cls) -> bool:
        try:
            return MessageMeta.objects.only('is_enabled').get(
                uuid=cls.uuid()
            ).is_enabled
        except MessageMeta.DoesNotExist:
            return True

    def send_message(self):
        if not self.is_enabled_message():
            return

        if not len(self.recipients):
            # Early check for empty list, for skip message generation
            return

        try:
            self.message = self.prepare_generalized_message()
        except NotImplementedError:
            self.message = ''

        if not len(self.message):
            # Don't send any messages, if it was empty
            return

        if self.personalized:
            self.send_personalized_message()
        else:
            self.send_bulk_message()

    def send_personalized_message(self):
        for recipient in self.recipients:
            vk_id = self.get_recipient_vk_id(recipient)
            vk_message_token = self.get_recipient_message_token(recipient)
            if not vk_id or not vk_message_token:
                # Skip users without vk params
                continue

            personalized_message = self.personalize(self.message, recipient)

            send_message(vk_id, vk_message_token, personalized_message)

    def send_bulk_message(self):
        send_bulk_message(
            [self.get_recipient_vk_id(x) for x in self.recipients],
            # TODO: to dispute what to do if in recipients list accidentally
            #  was added users from different company. Possible resolutions:
            #  1. Check in message init and raise ValueError
            #  2. Make bulk message params for every company
            self.get_recipient_message_token(self.recipients[0]),
            self.message
        )

    def prepare_generalized_message(self) -> str:
        return self.get_template().render(self.get_template_context())

    @classmethod
    def prepare_example_generalized_message(cls) -> str:
        return cls.get_template().render(cls.get_example_template_context())

    def get_template_context(self) -> Context:
        return Context()

    @classmethod
    def get_example_template_context(cls) -> Context:
        return Context({
            ctx_name: ctx.example
            for ctx_name, ctx in cls.template_args.items()
        })

    @classmethod
    def get_template(cls) -> Template:
        try:
            template_data = MessageMeta.objects.only('template').get(
                uuid=cls.uuid()
            ).template
            if not template_data:
                template_data = cls.default_template
        except MessageMeta.DoesNotExist:
            template_data = cls.default_template

        return Template(template_data)

    @staticmethod
    def get_recipient_vk_id(recipient: Recipient) -> Optional[int]:
        if isinstance(recipient, (Coach, Manager)):
            return recipient.user.vk_id

        # Don't explicit check recipient instance, as it was checked at init
        return recipient.vk_user_id

    @staticmethod
    def get_recipient_message_token(recipient: Recipient) -> Optional[str]:
        if isinstance(recipient, (Coach, Manager)):
            return recipient.user.vk_message_token

        # Don't explicit check recipient instance, as it was checked at init
        return recipient.vk_message_token

    @staticmethod
    def get_recipient_name(recipient: Recipient) -> str:
        if isinstance(recipient, (Coach, Manager)):
            return recipient.user.get_full_name()

        # Don't explicit check recipient instance, as it was checked at init
        return recipient.name

    def personalize(self, msg: str, recipient: Recipient) -> str:
        # Ignore check for empty msg, as at this moment it will be already
        # non empty
        fixed_msg = msg[0].lower() + msg[1:]
        name = self.get_recipient_name(recipient)

        return f'{name}, {fixed_msg}'
