import vk
import random
from datetime import datetime, date, time
import pytz

session = vk.Session()
api = vk.API(session, v=5.0)


def send_message(user_id, token, message, attachment=""):
    api.messages.send(access_token=token, user_id=str(user_id), message=message, attachment=attachment)