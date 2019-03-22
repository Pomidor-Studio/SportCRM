from typing import List, Sized

import vk
import vk.exceptions


def chunks(items: Sized, count: int):
    return [items[i:i + count] for i in range(0, len(items), count)]


def send_message(user_id: int, token: str, message: str, attachment: str = ''):
    if not message:
        # Silently fail if no message was provided
        return

    session = vk.Session()
    api = vk.API(session, v=5.90)

    try:
        api.messages.send(
            access_token=token, user_id=str(user_id), message=message,
            attachment=attachment
        )
    except vk.exceptions.VkAPIError:
        pass


def send_bulk_message(
    user_ids: List[int],
    token: str,
    message: str,
    attachment: str = ''
):
    if not message:
        # Silently fail if no message was provided
        return

    session = vk.Session()
    api = vk.API(session, v=5.90)

    for user_id_chunk in chunks(user_ids, 100):
        try:
            api.messages.send(
                access_token=token, user_ids=[str(x) for x in user_id_chunk],
                message=message, attachment=attachment
            )
        except vk.exceptions.VkAPIError:
            pass
