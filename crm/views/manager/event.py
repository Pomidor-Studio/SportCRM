from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
    TemplateView,
)
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import EventReportFilter
from crm.forms import EventAttendanceForm
from crm.models import Attendance, Event, EventClass
from crm.serializers import CalendarEventSerializer
from crm.tables import EventReportTable
from crm.views.mixin import UserManagerMixin


class Report(LoginRequiredMixin, UserManagerMixin, SingleTableMixin,  FilterView):
    table_class = EventReportTable
    template_name = 'crm/manager/event/report.html'
    filterset_class = EventReportFilter
    context_object_name = 'events'
    model = Event


class Calendar(PermissionRequiredMixin, TemplateView):
    permission_required = 'event'
    template_name = 'crm/manager/event/calendar.html'


class ApiCalendar(ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        first_day = timezone.now().replace(day=1).date()
        start = DateField().to_internal_value(
            self.request.query_params.get('start')
        ) or first_day

        end = DateField().to_internal_value(
            self.request.query_params.get('end')
        ) or (first_day + timedelta(days=31))

        events = []
        for ec in EventClass.objects.filter(
            Q(date_from__lte=end) &
            (Q(date_to__gte=start) | Q(date_to__isnull=True))
        ):
            events.extend(list(ec.get_calendar(start, end).values()))

        return events


class Create(LoginRequiredMixin, UserManagerMixin, RevisionMixin, CreateView):
    model = Event
    fields = '__all__'
    template_name = 'crm/manager/event/form.html'
    success_url = reverse_lazy('crm:manager:event:calendar')


class Update(LoginRequiredMixin, UserManagerMixin, RevisionMixin, UpdateView):
    model = Event
    fields = '__all__'
    template_name = 'crm/manager/event/form.html'
    success_url = reverse_lazy('crm:manager:event:calendar')


class Delete(LoginRequiredMixin, UserManagerMixin, RevisionMixin, DeleteView):
    model = Event
    template_name = 'crm/manager/event/confirm_delete.html'
    success_url = reverse_lazy('crm:manager:event:calendar')


class Detail(LoginRequiredMixin, UserManagerMixin, DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'crm/manager/event/detail.html'


class EventAttendanceCreate(
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    CreateView
):
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
