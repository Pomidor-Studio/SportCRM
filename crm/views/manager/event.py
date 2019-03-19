from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.views.generic import (
    TemplateView,
)
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import EventReportFilter
from crm.models import Event, EventClass
from crm.serializers import CalendarEventSerializer
from crm.tables import EventReportTable


class Report(PermissionRequiredMixin, SingleTableMixin,  FilterView):
    table_class = EventReportTable
    template_name = 'crm/manager/event/report.html'
    filterset_class = EventReportFilter
    context_object_name = 'events'
    model = Event
    permission_required = 'report.events'


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
