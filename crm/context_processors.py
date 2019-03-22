from django_multitenant.utils import get_current_tenant


def company(request):
    return {
        'company': get_current_tenant(),
    }
