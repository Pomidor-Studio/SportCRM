from django.contrib.auth.models import AnonymousUser
from django_multitenant.utils import set_current_tenant


def set_current_tenant_for_user(current_user):
    if isinstance(current_user, AnonymousUser):
        current_tenant = None
    elif current_user.is_manager or current_user.is_coach:
        current_tenant = current_user.company
    else:
        current_tenant = None

    set_current_tenant(current_tenant)


class SetTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        set_current_tenant_for_user(request.user)

        response = self.get_response(request)

        set_current_tenant(None)
        # Code to be executed for each request/response after
        # the view is called.

        return response
