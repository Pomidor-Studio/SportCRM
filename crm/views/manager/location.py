from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.models import Location


class ObjList(PermissionRequiredMixin, ListView):
    model = Location
    template_name = 'crm/manager/location/list.html'
    context_object_name = 'locations'
    ordering = ['id']
    permission_required = 'subscription'


class Create(PermissionRequiredMixin, RevisionMixin, CreateView):
    model = Location
    fields = ('name', 'address')
    template_name = 'crm/manager/location/form.html'
    permission_required = 'subscription.add'


class Update(PermissionRequiredMixin, RevisionMixin, UpdateView):
    model = Location
    fields = ('name', 'address')
    template_name = 'crm/manager/location/form.html'
    permission_required = 'subscription.edit'


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = Location
    success_url = reverse_lazy('crm:manager:locations:list')
    template_name = 'crm/manager/location/confirm_delete.html'
    permission_required = 'subscription.delete'
