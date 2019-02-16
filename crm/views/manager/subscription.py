from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from crm.models import SubscriptionsType
from crm.views.mixin import UserManagerMixin


class List(LoginRequiredMixin, UserManagerMixin, ListView):
    model = SubscriptionsType
    template_name = 'crm/manager/subscription/list.html'
    context_object_name = 'subscriptions'
    ordering = ['id']


class Create(LoginRequiredMixin, UserManagerMixin, CreateView):
    model = SubscriptionsType
    fields = '__all__'
    template_name = 'crm/manager/subscription/form.html'


class Update(LoginRequiredMixin, UserManagerMixin, UpdateView):
    model = SubscriptionsType
    fields = '__all__'
    template_name = 'crm/manager/subscription/form.html'


class Delete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_delete.html'
