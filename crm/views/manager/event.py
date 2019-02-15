from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from crm.forms import EventAttendanceForm
from crm.models import Event, Attendance
from crm.views.mixin import UserManagerMixin


class List(LoginRequiredMixin, UserManagerMixin, ListView):
    model = Event
    template_name = 'crm/manager/event/list.html'


class Create(LoginRequiredMixin, UserManagerMixin,CreateView):
    model = Event
    fields = '__all__'
    template_name = 'crm/manager/event/form.html'
    success_url = reverse_lazy('crm:manager:event:list')


class Update(LoginRequiredMixin, UserManagerMixin,UpdateView):
    model = Event
    fields = '__all__'
    template_name = 'crm/manager/event/form.html'
    success_url = reverse_lazy('crm:manager:event:list')


class Delete(LoginRequiredMixin, UserManagerMixin,DeleteView):
    model = Event
    template_name = 'crm/manager/event/confirm_delete.html'
    success_url = reverse_lazy('crm:manager:event:list')


class Detail(LoginRequiredMixin, UserManagerMixin, DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'crm/manager/event/detail.html'


class EventAttendanceCreate(LoginRequiredMixin, UserManagerMixin, CreateView):
    # TODO: Где должна использоваться эта View?
    model = Attendance
    form_class = EventAttendanceForm
    template_name = 'crm/manager/client/add-attendance.html'

    def get_initial(self):
        initial = super().get_initial()
        event = get_object_or_404(Event, pk=self.kwargs.get('event_id'))
        initial['event'] = event
        return initial

    def get_success_url(self):
        return reverse(
            'crm:manager:event:detail', args=[self.kwargs['event_id']])
