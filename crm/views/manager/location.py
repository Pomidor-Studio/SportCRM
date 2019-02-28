from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from reversion.views import RevisionMixin

from crm.models import Location
from crm.views.mixin import UserManagerMixin


class ObjList(LoginRequiredMixin, UserManagerMixin, ListView):
    model = Location
    template_name = 'crm/manager/location/list.html'
    context_object_name = 'locations'
    ordering = ['id']


class Create(LoginRequiredMixin, UserManagerMixin, RevisionMixin, CreateView):
    model = Location
    fields = ('name', 'address')
    template_name = 'crm/manager/location/form.html'


class Update(LoginRequiredMixin, UserManagerMixin, RevisionMixin, UpdateView):
    model = Location
    fields = ('name', 'address')
    template_name = 'crm/manager/location/form.html'


class Delete(LoginRequiredMixin, UserManagerMixin, RevisionMixin, DeleteView):
    model = Location
    success_url = reverse_lazy('crm:manager:locations:list')
    template_name = 'crm/manager/location/confirm_delete.html'
