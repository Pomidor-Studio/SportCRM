from uuid import UUID
from datetime import date, timedelta
from typing import List, Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView,
    TemplateView,
    RedirectView, FormView)
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.forms import DayOfTheWeekClassForm, EventAttendanceForm, EventClassForm, SubscriptionsTypeForm, \
    MarkClientWithoutSubscriptionForm
from crm.models import (Attendance, DayOfTheWeekClass, Event, EventClass, Client, ClientSubscriptions,
                        SubscriptionsType,
                        ClientAttendanceExists)
from crm.serializers import CalendarEventSerializer
from crm.views.mixin import UserManagerMixin, RedirectWithActionView


class ObjList(LoginRequiredMixin, UserManagerMixin, ListView):
    model = EventClass
    template_name = 'crm/manager/event_class/list.html'


class Delete(LoginRequiredMixin, UserManagerMixin, RevisionMixin, DeleteView):
    model = EventClass
    success_url = reverse_lazy('crm:manager:event-class:list')
    template_name = 'crm/manager/event_class/confirm_delete.html'


class Calendar(LoginRequiredMixin, UserManagerMixin, DetailView):
    model = EventClass
    context_object_name = 'event_class'
    template_name = 'crm/manager/event_class/calendar.html'


class ApiCalendar(ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        item_id = self.kwargs.get(self.lookup_field)
        first_day = timezone.now().replace(day=1).date()
        start = DateField().to_internal_value(
            self.request.query_params.get('start')
        ) or first_day

        end = DateField().to_internal_value(
            self.request.query_params.get('end')
        ) or (first_day + timedelta(days=31))
        return EventClass.objects.get(id=item_id).get_calendar(
            start, end
        ).values()


class EventByDateMixin:
    def get_object(self, queryset=None) -> Event:
        event_date = date(
            self.kwargs['year'], self.kwargs['month'], self.kwargs['day']
        )
        return Event.objects.get_or_virtual(
            self.kwargs['event_class_id'], event_date)


class EventByDate(
    PermissionRequiredMixin,
    EventByDateMixin,
    DetailView
):
    model = Event
    context_object_name = 'event'
    template_name = 'crm/manager/event/detail.html'
    permission_required = 'event'

    def get_clients_subscriptions(self, attendance_list, subscriptions):
        clients_subscriptions = {}
        attendance_client_list = [attendance.client for attendance in attendance_list]
        for subscription in subscriptions:
            client = subscription.client
            if client not in attendance_client_list:
                if client in clients_subscriptions.keys():
                    clients_subscriptions.get(client).append(subscription)
                else:
                    clients_subscriptions.update({client: [subscription]})
        return clients_subscriptions

    def get_clients_subscriptions_wattendance(self, attendance_list, subscriptions):
        clients_subscriptions = {}
        attendance_client_list = [attendance.client for attendance in attendance_list]
        for subscription in subscriptions:
            client = subscription.client
            if client in attendance_client_list:
                if client in clients_subscriptions.keys():
                    clients_subscriptions.get(client).append(subscription)
                else:
                    clients_subscriptions.update({client: [subscription]})
        return clients_subscriptions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        marked_clients = Client.objects.with_active_subscription_to_event(self.object).filter(
            attendance__event__event_class=self.object.event_class,
            attendance__marked = True
        )
        signed_up_clients = Client.objects.with_active_subscription_to_event(self.object).filter(
            attendance__event__event_class = self.object.event_class,
            attendance__marked=False,
            attendance__signed_up=True
        )

        for client in signed_up_clients:
            subs = client.clientsubscriptions_set.all()

        unmarked_clients = Client.objects.with_active_subscription_to_event(self.object).exclude(
             clientsubscriptions__subscription__event_class = self.object.event_class,
             attendance__event__event_class=self.object.event_class,
        )

        attendance_list = self.object.attendance_set.all().select_related('client').order_by('client__name')
        attendance_list_signed_up = self.object.attendance_set.filter(signed_up=True, marked=False).select_related('client').order_by('client__name')
        event_class = self.object.event_class
        subscriptions_types = SubscriptionsType.objects.filter(event_class=event_class)
        subscriptions = ClientSubscriptions.objects.filter(subscription__in=subscriptions_types,
                                                           start_date__lte=self.object.date,
                                                           end_date__gte=self.object.date,
                                                           visits_left__gt=0)
        clients_subscriptions = self.get_clients_subscriptions(attendance_list, subscriptions)
        clients_subscriptions_wattendance = self.get_clients_subscriptions_wattendance(attendance_list_signed_up, subscriptions)

        context.update({
            'attendance_list' : attendance_list,
            'clients_subscriptions' : clients_subscriptions,
            'clients_subscriptions_wattendance' : clients_subscriptions_wattendance,
            'marked_clients': marked_clients,
            'signed_up_clients': signed_up_clients,
            'unmarked_clients': unmarked_clients
        })

        return context


class CancelWithoutExtending(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView,
):
    permission_required = 'event.cancel'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.cancel_event(extend_subscriptions=False)


class CancelWithExtending(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView,
):
    permission_required = 'event.cancel'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.cancel_event(extend_subscriptions=True)


class ActivateWithoutRevoke(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView,
):
    permission_required = 'event.activate'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.activate_event(revoke_extending=False)


class ActivateWithRevoke(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView,
):
    permission_required = 'event.activate'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.activate_event(revoke_extending=True)


class MarkEventAttendance(
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    CreateView
):
    template_name = 'crm/manager/client/add-attendance.html'
    form_class = EventAttendanceForm

    def get_object(self, queryset=None):
        event_date = date(
            self.kwargs['year'], self.kwargs['month'], self.kwargs['day']
        )
        event, _ = Event.objects.get_or_create(
            event_class_id=self.kwargs['event_class_id'],
            date=event_date)

        return Attendance(event=event)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.get_object()})
        return kwargs

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class UnMarkClient(
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    RedirectView
):
    def get(self, request, *args, **kwargs):
        event_date = date(self.kwargs['year'],
                          self.kwargs['month'],
                          self.kwargs['day'])
        event, _ = Event.objects.get_or_create(event_class_id=self.kwargs['event_class_id'],
                                               date=event_date)
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.restore_visit(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class SignUpClient(
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    RedirectView
):

    def get(self, request, *args, **kwargs):
        event_date = date(self.kwargs['year'],
                          self.kwargs['month'],
                          self.kwargs['day'])
        event, _ = Event.objects.get_or_create(event_class_id=self.kwargs['event_class_id'],
                                               date=event_date)
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.signup_for_event(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class MarkClientWithoutSubscription (
    PermissionRequiredMixin,
    RevisionMixin,
    FormView
):
    form_class = MarkClientWithoutSubscriptionForm
    template_name = 'crm/manager/event/mark_client_without_sub.html'
    permission_required = 'is_manager'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_date = date(self.kwargs['year'],
                          self.kwargs['month'],
                          self.kwargs['day'])
        event, _ = Event.objects.get_or_create(event_class_id=self.kwargs['event_class_id'],
                                               date=event_date)
        context.update({
            'event': event
        })
        return context

    def form_valid(self, form):
        clients = form.cleaned_data['client']
        event_date = date(self.kwargs['year'],
                          self.kwargs['month'],
                          self.kwargs['day'])
        event, _ = Event.objects.get_or_create(event_class_id=self.kwargs['event_class_id'],
                                               date=event_date)
        for client in clients:
            client.signup_for_event(event)
        return super(MarkClientWithoutSubscription, self).form_valid(form)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class MarkClient (
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    RedirectView
):

    def get(self, request, *args, **kwargs):
        event_date = date(self.kwargs['year'],
                          self.kwargs['month'],
                          self.kwargs['day'])
        event, _ = Event.objects.get_or_create(event_class_id=self.kwargs['event_class_id'],
                                               date=event_date)
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.mark_visit(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class CreateEdit(
    LoginRequiredMixin,
    UserManagerMixin,
    RevisionMixin,
    TemplateView
):

    template_name = 'crm/manager/event_class/form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None
        self.weekdays: List[Optional[DayOfTheWeekClassForm]] = [None] * 7
        self.form: EventClassForm = None

    def get_object(self):
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(EventClass, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'eventclass_form': self.form,
            'weekdays': self.weekdays
        })
        return context

    def get(self, request, *args, **kwargs):
        self.get_object()
        prefiled_days = {}
        if self.object:
            # Получаем уже записанные дни для тип тренировки
            prefiled_days = {
                x.day: x for x in self.object.dayoftheweekclass_set.all()
            }

        self.form = EventClassForm(instance=self.object)

        # Заполняем форму дней тренировки
        for i in range(7):
            sub_form_obj = prefiled_days.get(
                i, DayOfTheWeekClass(event=self.object, day=i))
            self.weekdays[i] = DayOfTheWeekClassForm(
                instance=sub_form_obj,
                prefix=f'weekday{i}',
                initial={'checked': bool(sub_form_obj.id)}
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_object()

        self.form = EventClassForm(request.POST, instance=self.object)
        with transaction.atomic():
            self.object = self.form.save()

            # сохраняем или удаляем дни недели, которые уже
            # были у тренировки ранее
            for weekday in self.object.dayoftheweekclass_set.all():
                weekdayform = DayOfTheWeekClassForm(
                    request.POST,
                    prefix=f'weekday{weekday.day}',
                    instance=weekday)
                if weekdayform.is_valid():
                    if weekdayform.cleaned_data['checked']:
                        weekdayform.save()
                    else:
                        weekday.delete()
                self.weekdays[weekday.day] = weekdayform

            # Проверяем все остальные дни
            for i in range(7):
                if not self.weekdays[i]:
                    weekday = DayOfTheWeekClass(day=i)
                    weekdayform = DayOfTheWeekClassForm(
                        request.POST, prefix=f'weekday{i}', instance=weekday)
                    if weekdayform.is_valid():
                        if weekdayform.cleaned_data['checked']:
                            weekdayform.instance.event = self.object
                            weekdayform.save()
                    self.weekdays[i] = weekdayform

        return HttpResponseRedirect(reverse(
            'crm:manager:event-class:update', kwargs={'pk': self.object.id}))


class Scanner(
    PermissionRequiredMixin,
    EventByDateMixin,
    TemplateView
):
    permission_required = 'event.mark_attendance'
    template_name = 'crm/manager/event/scanner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.get_object()
        return context


class DoScan(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView
):
    permission_required = 'event.mark_attendance'
    pattern_name = 'crm:manager:event-class:event:scanner'

    def run_action(self):
        code = self.kwargs.get('code')

        if not code:
            messages.error(self.request, 'Не передан код')
            return
        try:
            uuid = UUID(code)
        except ValueError:
            messages.error(self.request, f'Некорректный формат кода "{code}"')
            return

        try:
            client = Client.objects.get(qr_code=uuid)
        except Client.DoesNotExist:
            messages.error(self.request, f'Ученик с QR кодом {code} не найден')
            return
        event = self.get_object()
        subscription = ClientSubscriptions.objects.active_subscriptions(event).filter(
            client=client).order_by(
            'purchase_date').first()
        if not subscription:
            messages.warning(self.request, f'У {client} нет действующего абонемента')
            return
        try:
            subscription.mark_visit(event)
        except ClientAttendanceExists:
            messages.warning(self.request, f'{client} уже отмечен')
        else:
            messages.info(self.request, f'{client} отмечен по абонементу {subscription}')
            return

    def get_redirect_url(self, *args, **kwargs):
        kwargs.pop('code')
        return super().get_redirect_url(*args, **kwargs)


class DoCloseEvent(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView
):
    permission_required = 'event.mark_attendance'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.close_event()
        return


class DoOpenEvent(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView
):
    permission_required = 'event.mark_attendance'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.open_event()
        return
