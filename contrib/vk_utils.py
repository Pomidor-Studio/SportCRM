import functools

import vk
from django.conf import settings


def use_vk_api(func):
    @functools.wraps(func)
    def decorator(*args):
        session = vk.Session()
        api = vk.API(session, v=5.90)
        return func(*args, vk_api=api)

    return decorator


@use_vk_api
def get_vk_user_info(vk_user_ids, vk_api=None):
    if isinstance(vk_user_ids, (int, str)):
        vk_user_ids = [vk_user_ids]

    results = vk_api.users.get(
        access_token=settings.VK_GROUP_TOKEN,
        user_ids=','.join([str(x) for x in vk_user_ids]),
        fields='photo_100,bdate,domain'
    )

    ret = {}
    for result in results:
        ret[result['id']] = result

    return ret
