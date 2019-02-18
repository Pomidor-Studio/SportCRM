from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from crm.views.mixin import UserManagerMixin


class Home(LoginRequiredMixin, UserManagerMixin, TemplateView):
    template_name = 'crm/base.html'
