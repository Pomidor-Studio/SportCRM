from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, UpdateView
from django_filters.views import FilterView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import LocationFilter
from crm.models import Location
from crm.views.mixin import UnDeleteView, CreateAndAddView


class List(PermissionRequiredMixin, FilterView):
    model = Location
    template_name = 'crm/manager/location/list.html'
    context_object_name = 'locations'
    ordering = ['id']
    paginate_by = 25
    permission_required = 'location'
    filterset_class = LocationFilter


class Create(PermissionRequiredMixin, RevisionMixin, CreateAndAddView):
    model = Location
    fields = ('name', 'address')
    template_name = 'crm/manager/location/form.html'
    permission_required = 'location.add'
    add_another_url = 'crm:manager:locations:new'
    message_info = 'Место успешно создано'


class Update(PermissionRequiredMixin, RevisionMixin, UpdateView):
    model = Location
    fields = ('name', 'address')
    template_name = 'crm/manager/location/form.html'
    permission_required = 'location.edit'


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = Location
    success_url = reverse_lazy('crm:manager:locations:list')
    context_object_name = 'location'
    template_name = 'crm/manager/location/confirm_delete.html'
    permission_required = 'location.delete'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        if self.object.has_active_events:
            messages.warning(self.request, f'Локация {self.object} удалена. На локации остались активные тренировки!')
        else:
            messages.info(self.request, f'Локация {self.object} удалена.')
        self.object.delete()

        return HttpResponseRedirect(success_url)


class Undelete(
    PermissionRequiredMixin,
    RevisionMixin,
    UnDeleteView
):
    template_name = 'crm/manager/location/confirm_undelete.html'
    model = Location
    context_object_name = 'location'
    success_url = reverse_lazy('crm:manager:locations:list')
    permission_required = 'location.undelete'

    def undelete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.undelete()
        messages.info(self.request, f'Локация {self.object} возвращена.')
        return HttpResponseRedirect(success_url)
