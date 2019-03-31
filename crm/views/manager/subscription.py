from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, UpdateView
from django_filters.views import FilterView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import SubscriptionsTypeFilterSet
from crm.forms import SubscriptionsTypeForm
from crm.models import SubscriptionsType
from crm.views.mixin import UnDeleteView, CreateAndAddMixin


class List(PermissionRequiredMixin, FilterView):
    model = SubscriptionsType
    template_name = 'crm/manager/subscription/list.html'
    context_object_name = 'subscriptions'
    ordering = ['id']
    filterset_class = SubscriptionsTypeFilterSet
    permission_required = 'subscription'


class Create(PermissionRequiredMixin, RevisionMixin, CreateAndAddMixin):
    model = SubscriptionsType
    form_class = SubscriptionsTypeForm
    template_name = 'crm/manager/subscription/form.html'
    permission_required = 'subscription.add'
    add_another_url = 'crm:manager:subscription:new'


class Update(PermissionRequiredMixin, RevisionMixin, UpdateView):
    permission_required = 'subscription.edit'
    model = SubscriptionsType
    form_class = SubscriptionsTypeForm
    template_name = 'crm/manager/subscription/form.html'


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_delete.html'
    permission_required = 'subscription.delete'


class UnDelete(PermissionRequiredMixin, RevisionMixin, UnDeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_undelete.html'
    permission_required = 'subscription.undelete'
