from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.checks import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django_filters.views import FilterView
from reversion.views import RevisionMixin

from crm.filters import LocationFilter
from crm.models import Location
from crm.views.mixin import UserManagerMixin, UnDeleteView


class ObjList(LoginRequiredMixin, UserManagerMixin, FilterView):
    model = Location
    template_name = 'crm/manager/location/list.html'
    context_object_name = 'locations'
    ordering = ['id']
    filterset_class = LocationFilter


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

class Undelete(
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    UnDeleteView
):
    template_name = 'crm/manager/coach/confirm_undelete.html'
    model = Location
    context_object_name = 'location'
    success_url = reverse_lazy('crm:manager:location:list')

    def undelete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        success_url = self.get_success_url()
        self.object.undelete()
        user.is_active = True
        user.save()
        messages.info(self.request, f'Место {self.object} возвращено.')
        return HttpResponseRedirect(success_url)
