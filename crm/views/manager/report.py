from django.views.generic import TemplateView
from rules.contrib.views import PermissionRequiredMixin


class ReportList(PermissionRequiredMixin, TemplateView):
    permission_required = 'report.list'
    template_name = 'crm/manager/reports.html'
