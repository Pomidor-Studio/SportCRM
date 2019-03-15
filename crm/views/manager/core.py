from django.views.generic import TemplateView
from rules.contrib.views import PermissionRequiredMixin


class Home(PermissionRequiredMixin, TemplateView):
    template_name = 'crm/base.html'
    permission_required = 'is_manager'
