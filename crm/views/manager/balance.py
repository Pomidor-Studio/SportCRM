from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.forms import Balance
from crm.models import Client, ClientBalanceChangeHistory


class Create(PermissionRequiredMixin, RevisionMixin, CreateView):
    model = ClientBalanceChangeHistory
    template_name = 'crm/manager/balance/form.html'
    permission_required = 'client-balance.add'
    form_class = Balance

    def get_initial(self):
        initial = super().get_initial()
        initial['client'] = self.get_client()
        return initial

    def get_client(self) -> Client:
        return get_object_or_404(Client, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'client': self.get_client()
        })
        return context

    def get_success_url(self):
        return reverse('crm:manager:client:detail', args=[self.kwargs['pk']])

    def form_valid(self, form):
        with transaction.atomic():
            self.get_client().update_balance(form.cleaned_data['change_value'])
            return super().form_valid(form)

