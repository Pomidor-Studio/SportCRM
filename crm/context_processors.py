from django.conf import settings
from django_multitenant.utils import get_current_tenant


def company(request):
    return {
        'company': get_current_tenant(),
    }


def vk_site_access_token(request):
    return {
        'vk_site_access_token': settings.VK_GROUP_TOKEN
    }
