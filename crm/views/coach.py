from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from crm.views.mixin import UserCoachMixin


class HomePage(LoginRequiredMixin, UserCoachMixin, TemplateView):
    template_name = 'crm/coach/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['coach'] = self.request.user.coach
        return context
