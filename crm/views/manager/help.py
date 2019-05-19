from django.views.generic import TemplateView
from django.conf import settings

from rules.contrib.views import PermissionRequiredMixin


class Help(PermissionRequiredMixin, TemplateView):
    template_name = 'crm/manager/help/help.html'
    permission_required = 'manager'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['support_group_id'] = settings.SUPPORT_GROUP_ID
        return data

