import vk
import vk.exceptions


def send_message(user_id: int, token: str, message: str, attachment: str = ''):
    if message is None or not len(message):
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
