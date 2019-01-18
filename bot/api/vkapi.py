import vk

session = vk.Session()
api = vk.API(session, v=5.5)


def send_message(user_id, token, message, attachment=""):
    api.messages.send(access_token=token, user_id=str(user_id), message=message, attachment=attachment)