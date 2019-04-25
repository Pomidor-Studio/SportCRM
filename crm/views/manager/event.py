from datetime import timedelta
from itertools import chain

from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from django.views.generic import (
    TemplateView,
    FormView,
)
from django.contrib import messages
from dateutil.relativedelta import relativedelta
from django_tables2 import SingleTableMixin
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import EventReportFilter
from crm.models import EventClass, Event, ClientSubscriptions, User
from crm.serializers import CalendarEventSerializer
from crm.tables import ReportTable


class Report(PermissionRequiredMixin, SingleTableMixin, FormView):
    table_class = ReportTable
    template_name = 'crm/manager/event/report.html'
    permission_required = 'report.events'
    form_class = EventReportFilter

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.request.GET
        return kwargs

    def _event_data(self, date, employee=None, event_class=None):
        fltr = {
            'date__range': date,
        }
        if employee:
            fltr['event_class__coach__user__in'] = employee
        if event_class:
            fltr['event_class__in'] = event_class

        events = Event.objects.select_related(
            'event_class'
        ).filter(
            **fltr
        ).iterator()
        for event in events:
            yield {
                'date': event.date,
                'employee': event.event_class.coach,
                'event_class': event.event_class,
                'clients_count': event.get_present_clients_count(),
                'clients_count_one_time': event.get_clients_count_one_time_sub(),
                'subs_sales': event.get_subs_sales(),
                'profit': event.get_profit()
            }

    def _client_subscriptions_data(self, date, employee=None):
        fltr = {
            'purchase_date__range': date,
        }
        if employee:
            fltr['sold_by__in'] = employee

        subscriptions = ClientSubscriptions.objects.filter(
            event__isnull=True,
            **fltr,
        ).values(
            'purchase_date',
            'sold_by'
        ).annotate(
            profit=Sum('price')
        ).iterator()
        for subscription in subscriptions:
            yield {
                'date': subscription['purchase_date'],
                'employee': User.objects.filter(id=subscription['sold_by']).first(),
                'event_class': None,
                'clients_count': None,
                'clients_count_one_time': None,
                'subs_sales': None,
                'profit': subscription['profit']
            }

    def date_filter(self, value):
        if value:
            start = value.start
            stop = value.stop
            start_plus_n_months = start + relativedelta(months=settings.MAX_REPORT_PERIOD_IN_MONTHS)
            if stop > start_plus_n_months:
                messages.warning(
                    self.request,
                    f'Период построения отчета не может превышать {settings.MAX_REPORT_PERIOD_IN_MONTHS} месяца.'
                )
                return None, None
            return start, stop
        return None, None

    def get_table_data(self):
        form = self.get_form()
        if form.is_valid():
            params = {
                'date': self.date_filter(form.cleaned_data['date']),
                'employee': form.cleaned_data['employee'] or None,
            }
            return chain(
                self._event_data(**params, event_class=form.cleaned_data['event_class']),
                self._client_subscriptions_data(**params)
            )
        else:
            return []


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
        for ec in EventClass.objects.in_range(start, end):
            events.extend(list(ec.get_calendar(start, end).values()))

        return events
