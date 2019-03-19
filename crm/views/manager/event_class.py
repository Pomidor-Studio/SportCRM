from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    DeleteView, DetailView, ListView, RedirectView, TemplateView,
)
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.enums import GRANULARITY
from crm.forms import DayOfTheWeekClassForm, EventClassForm
from crm.models import (
    Client, ClientAttendanceExists, ClientSubscriptions,
    DayOfTheWeekClass, Event, EventClass, SubscriptionsType,
)
from crm.serializers import CalendarEventSerializer
from crm.views.mixin import RedirectWithActionView


class ObjList(PermissionRequiredMixin, ListView):
    model = EventClass
    template_name = 'crm/manager/event_class/list.html'
    permission_required = 'event_class'


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = EventClass
    success_url = reverse_lazy('crm:manager:event-class:list')
    template_name = 'crm/manager/event_class/confirm_delete.html'
    permission_required = 'event_class.delete'


class Calendar(PermissionRequiredMixin, DetailView):
    model = EventClass
    context_object_name = 'event_class'
    template_name = 'crm/manager/event_class/calendar.html'
    permission_required = 'event'


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

    def get_clients_subscriptions(self, clients_qs, event: Event):
        result = {}
        for client in clients_qs:
            result.update({client:[]})
            subs = client.clientsubscriptions_set.active_subscriptions(event)
            for sub in subs:
                result.get(client).append(sub)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        signed_up_clients_qs = Client.objects.filter(
            attendance__event=self.object,
            attendance__marked=False,
            attendance__signed_up=True
        )
        signed_up_clients = self.get_clients_subscriptions(signed_up_clients_qs, self.object)
        unmarked_clients_qs = Client.objects.with_active_subscription_to_event(self.object).filter(
            attendance__isnull=True
        )
        unmarked_clients = self.get_clients_subscriptions(unmarked_clients_qs, self.object)
        attendance_list_marked = self.object.attendance_set.filter(marked=True).select_related('client').order_by('client__name')

        context.update({
            'attendance_list_marked' : attendance_list_marked,
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
    PermissionRequiredMixin,
    RevisionMixin,
    CreateView
):
    permission_required = 'event.mark-attendance'
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
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event.mark-attendance'

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.restore_visit(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class SignUpClient(
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event'

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.signup_for_event(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class CancelAttendance(
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event'

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.cancel_signup_for_event(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class SignUpClientWithoutSubscription (
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    FormView
):
    form_class = SignUpClientWithoutSubscriptionForm
    template_name = 'crm/manager/event/mark_client_without_sub.html'
    permission_required = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        context.update({
            'event': event
        })
        return context

    def form_valid(self, form):
        clients = form.cleaned_data['client']
        event = self.get_object()
        for client in clients:
            client.signup_for_event(event)
        return super(SignUpClientWithoutSubscription, self).form_valid(form)

    def get_success_url(self):
        return reverse('crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class MarkClient (
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event'

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        client_id = self.kwargs.pop('client_id')
        subscription_id = self.kwargs.pop('subscription_id')
        client = Client.objects.get(id=client_id)
        client_sub = ClientSubscriptions.objects.get(id=subscription_id)
        client.mark_visit(event, client_sub)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class CreateEdit(
    PermissionRequiredMixin,
    RevisionMixin,
    TemplateView
):

    template_name = 'crm/manager/event_class/form.html'
    permission_required = 'event_class.add'

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

        #Заполняем стоимость одноразового посещения
        try:
            one_time_sub = SubscriptionsType.objects.get(one_time=True, event_class=self.object)
            self.form.fields['one_time_price'].initial = one_time_sub.price
        except SubscriptionsType.DoesNotExist:
            one_time_sub = None

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_object()

        self.form = EventClassForm(request.POST, instance=self.object)
        with transaction.atomic():
            self.object = self.form.save()
            #Добавляем абонемент на разовое посещение, если цена указана и не равна нулю
            one_time_price = self.form.cleaned_data['one_time_price']
            name = self.object.name
            try:
                one_time_sub = SubscriptionsType.all_objects.get(one_time=True, event_class=self.object)
                if one_time_price and one_time_price > 0:
                    if one_time_sub.deleted:
                        one_time_sub.undelete()
                    one_time_sub.price = one_time_price
                    one_time_sub.save()
                else:
                    one_time_sub.delete()
            except SubscriptionsType.DoesNotExist:
                if one_time_price and one_time_price > 0:
                    sub = SubscriptionsType(
                        name='Разовое посещение ' + name,
                        price=one_time_price,
                        duration_type=GRANULARITY.DAY,
                        duration=1,
                        rounding=False,
                        visit_limit=1,
                        one_time=True
                    )
                    sub.save()
                    sub.event_class.add(self.object)

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
    permission_required = 'event.mark-attendance'
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
    permission_required = 'event.mark-attendance'
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
    permission_required = 'event.mark-attendance'
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
    permission_required = 'event.mark-attendance'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.open_event()
        return
