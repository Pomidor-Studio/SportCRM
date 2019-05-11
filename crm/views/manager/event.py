from datetime import timedelta, date

from typing import Dict, List

from django.utils import timezone
from django.views.generic import (
    TemplateView,
    FormView,
)
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import EventReportFilter, VisitReportFilter
from crm.models import EventClass, Event, ClientSubscriptions, Attendance
from crm.serializers import CalendarEventSerializer
from crm.tables import EventReportTable


class EventReport(PermissionRequiredMixin, SingleTableMixin, FilterView):
    table_class = EventReportTable
    template_name = 'crm/manager/event/report.html'
    filterset_class = EventReportFilter
    context_object_name = 'events'
    model = Event
    permission_required = 'report.events'


class VisitReport(PermissionRequiredMixin, FormView):
    template_name = 'crm/manager/event/visit-report.html'
    permission_required = 'report.events'
    form_class = VisitReportFilter

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.request.GET
        return kwargs

    def get_month_dates_range(self, year: int, month: int):
        dt = date.today().replace(year, month)
        days = (dt.replace(month=month % 12 + 1, day=1) - timedelta(days=1)).day
        dates = []
        for day in range(1, days + 1):
            dates.append(dt.replace(day=day))
        return dates

    def get_context_data(self, **kwargs: dict):
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        if form.is_valid():
            month = int(form.cleaned_data['month'])
            year = int(form.cleaned_data['year'])
            event_class = form.cleaned_data['event_class']
        else:
            month = date.today().month
            year = date.today().year
            event_class = None
        context['month'] = month
        context['year'] = year
        context['years'] = range(2019, date.today().year + 1)
        dates = self.get_month_dates_range(year, month)
        context['month_days'] = range(1, len(dates) + 1)
        data = self.get_table_data(year, month, event_class)
        context['table_data'] = self.sort_data(data)
        return context

    def sort_data(self, data: list) -> List[dict]:
        data.sort(key=lambda i: '' if i['subscription'] != 'Разовые' else i['subscription'])
        data.sort(key=lambda i: i['client'].name)
        return data

    def get_table_data(self, year: int, month: int, event_classes):
        data = self.get_subscription_visits(year, month, event_classes)

        for client, attendances in self.get_one_time_visits(year, month, event_classes).items():
            data.append({
                'client': client,
                'subscription': 'Разовые',
                'visit_start': 0,
                'visit_end': 0,
                'attendances': attendances
            })
        return data

    def get_subscription_visits(self, year: int, month: int, event_classes):
        dates = self.get_month_dates_range(year, month)
        from_date, to_date = dates[0], dates[-1]
        fltr = {
            'subscription__one_time': False,
            'start_date__lte': to_date,
            'end_date__gte': from_date,
        }
        if event_classes:
            fltr['subscription__event_class__in'] = event_classes

        active_subs = ClientSubscriptions.objects.exclude_onetime().filter(
           **fltr
        ).select_related(
            'subscription', 'client'
        ).iterator()

        result = []
        for subs in active_subs:
            attendances = ['grey'] * len(dates)
            from_date_ = max(from_date, subs.start_date)
            to_date_ = min(to_date, subs.end_date or to_date)
            # Фикс для абоенментов из будущего
            if to_date_ > from_date_:
                from_date_ = from_date
                to_date_ = to_date

            for event in subs.subscription.events_to_date(from_date=from_date_, to_date=to_date_):
                attendances[event.date.day - 1] = 'red'

            visit_start = subs.visits_on_by_time
            if subs.start_date < from_date:
                visit_start -= subs.attendance_set.filter(
                    marked=True,
                    event__date__lt=from_date,
                    event__is_closed=True,
                ).count()

            visited = subs.attendance_set.filter(
                marked=True,
                event__date__range=(from_date, to_date),
                event__is_closed=True,
            ).select_related('event').all()

            for visit in visited:
                attendances[visit.event.date.day - 1] = 'green'
            visit_end = visit_start - len(visited)

            result.append({
                'client': subs.client,
                'subscription': subs.subscription.name,
                'attendances': attendances,
                'visit_start': visit_start,
                'visit_end': visit_end,
            })
        return result

    def get_one_time_visits(self, year: int, month: int, event_classes) -> Dict:
        dates = self.get_month_dates_range(year, month)
        fltr = {
            'subscription__subscription__one_time': True,
            'event__is_closed': True,
            'event__date__range': (dates[0], dates[-1])
        }
        if event_classes:
            fltr['event__event_class__in'] = event_classes

        attendances = Attendance.objects.filter(
            **fltr
        ).select_related('client', 'event').all()
        result = {}
        for attendance in attendances:
            client = attendance.client
            if client not in result:
                result[client] = ['grey'] * len(dates)
            day = attendance.event.date.day
            result[client][day - 1] = 'green'
        return result


class Calendar(PermissionRequiredMixin, TemplateView):
    permission_required = 'event'
    template_name = 'crm/manager/event/calendar.html'


class ApiCalendar(ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        first_day = timezone.now().replace(day=1).date()
        start = DateField().to_internal_value(
            self.request.query_params.get('start').split('T')[0]
        ) or first_day

        end = DateField().to_internal_value(
            self.request.query_params.get('end').split('T')[0]
        ) or (first_day + timedelta(days=31))

        events = []
        for ec in EventClass.objects.in_range(start, end):
            events.extend(list(ec.get_calendar(start, end).values()))

        return events
