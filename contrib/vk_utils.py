import functools
import re
from typing import Optional, Dict, Sequence, Union

import vk
from django.conf import settings

VK_PAGE_REGEXP = re.compile('(https?://)?vk.com/(?P<user_id>([A-Za-z0-9_])+)')


def get_vk_id_from_link(vk_link) -> Optional[str]:
    """
    Get user vk id or domain from URI

    :param vk_link: URI of person VK page
    :return: VK id or domain
    """
    match = VK_PAGE_REGEXP.match(vk_link)
    return match.group('user_id') if match else None


def use_vk_api(func):
    @functools.wraps(func)
    def decorator(*args):
        session = vk.Session()
        api = vk.API(session, v=5.90)
        return func(*args, vk_api=api)

    return decorator


@use_vk_api
def get_one_vk_user_info(
    vk_user_id: Union[int, str],
    vk_api: vk.API
) -> Optional[Dict]:
    """
    Get information about *one* VK user. For batch request use get_vk_user_info

    :param vk_user_id: VK user id or domain
    :param vk_api:  VK API object

    :return: VK information about person
    """
    results = vk_api.users.get(
        access_token=settings.VK_GROUP_TOKEN,
        user_ids=vk_user_id,
        fields='photo_100,bdate,domain'
    )

    try:
        return results[0]
    except IndexError:
        return None


@use_vk_api
def get_vk_user_info(
    vk_user_ids: Union[int, str, Sequence],
    vk_api: vk.API
) -> Dict[str, Dict]:
    """
    Get information about list of users. Can handle and one id as argument,
    but result always will be dictionary.

    :param vk_user_ids: VK user id or domain, can be placed in list container
    :param vk_api: VK API object
    :return: Information about all passed users
    """
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


def get_vk_id_from_page_link(vk_page: str) -> Union[None, int]:
    if not vk_page:
        return
    try:
        vk_id = get_vk_id_from_link(vk_page)
        if not vk_id:
            return
        vk_user = get_one_vk_user_info(vk_id)
        if not vk_user:
            return
    except Exception:
        return
    return vk_user['id']
