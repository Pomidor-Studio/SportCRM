from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django_multitenant.utils import get_current_tenant

from crm.forms import CompanyForm
from crm.models import Company


class Edit(UpdateView):
    form_class = CompanyForm
    template_name = 'crm/manager/company/form.html'
    model = Company
    success_url = reverse_lazy('crm:manager:company')

    def get_object(self, queryset=None):
        return get_current_tenant()
