from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.views.generic import RedirectView


class SportCrmLoginRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_coach:
            return resolve_url('crm:coach.home')
        elif self.request.user.is_manager:
            return resolve_url('crm:base')
        else:
            raise PermissionDenied()
