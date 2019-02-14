from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import RedirectView


class SportCrmLoginRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_coach:
            return reverse('crm:coach:home')
        elif self.request.user.is_manager:
            return reverse('crm:base')
        else:
            raise PermissionDenied()
