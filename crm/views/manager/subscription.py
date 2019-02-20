from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django_filters.views import FilterView

from crm.filters import SubscriptionsTypeFilterSet
from crm.forms import SubscriptionsTypeForm
from crm.models import SubscriptionsType
from crm.views.mixin import UserManagerMixin, UnDeleteView


class List(LoginRequiredMixin, UserManagerMixin, FilterView):
    model = SubscriptionsType
    template_name = 'crm/manager/subscription/list.html'
    context_object_name = 'subscriptions'
    ordering = ['id']
    filterset_class = SubscriptionsTypeFilterSet


class Create(LoginRequiredMixin, UserManagerMixin, CreateView):
    model = SubscriptionsType
    form_class = SubscriptionsTypeForm
    template_name = 'crm/manager/subscription/form.html'


class Update(LoginRequiredMixin, UserManagerMixin, UpdateView):
    model = SubscriptionsType
    form_class = SubscriptionsTypeForm
    template_name = 'crm/manager/subscription/form.html'


class Delete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_delete.html'


class UnDelete(LoginRequiredMixin, UserManagerMixin, UnDeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_undelete.html'
