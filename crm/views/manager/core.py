from django.views.generic import TemplateView


class Home(PermissionRequiredMixin, TemplateView):
    template_name = 'crm/base.html'
    permission_required = 'is_manager'
