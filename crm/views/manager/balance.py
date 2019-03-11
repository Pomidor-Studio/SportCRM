from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView
from rules.contrib.views import PermissionRequiredMixin

from crm.forms import Balance
from crm.models import ClientBalance, Client


class Create(PermissionRequiredMixin, CreateView):
    model = ClientBalance
    template_name = 'crm/manager/balance/form.html'
    permission_required = 'client-balance.add'
    form_class = Balance

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'client_id': self.kwargs['pk']
        })
        return context

    def get_success_url(self):
        return reverse('crm:manager:client:detail', args=[self.kwargs['pk']])

    def form_valid(self, form):
        client_id = self.kwargs['pk']
        form.instance.client_id = client_id
        Client.objects.get(id=client_id).update_balance(form.instance.balance)
        return super().form_valid(form)

