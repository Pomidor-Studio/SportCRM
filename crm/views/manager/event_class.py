import datetime
import json
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, RedirectView,
    TemplateView,
)
from rest_framework.fields import DateField
from rest_framework.generics import (CreateAPIView, ListAPIView, UpdateAPIView)
from rest_framework.permissions import IsAuthenticated
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.forms import (
    ClientForm, InplaceSellSubscriptionForm, SignUpClientMultiForm,
)
from crm.models import (
    Client, ClientAttendanceExists, ClientSubscriptions, Coach, Event,
    EventClass, Location, SubscriptionsType,
)
from crm.serializers import CalendarEventSerializer, EventClassEditSerializer
from crm.views.mixin import RedirectWithActionView
from gcp.tasks import enqueue


class ObjList(PermissionRequiredMixin, ListView):
    model = EventClass
    template_name = 'crm/manager/event_class/list.html'
    permission_required = 'event_class'


class Detail(PermissionRequiredMixin, DetailView):
    model = EventClass
    context_object_name = 'event_class'
    template_name = 'crm/manager/event_class/detail.html'
    permission_required = 'event_class.detail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['go_back'] = self.request.GET.get('gb')
        context['days'] = {
            x.day: x for x in self.object.dayoftheweekclass_set.all()
        }
        return context


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = EventClass
    success_url = reverse_lazy('crm:manager:event-class:list')
    template_name = 'crm/manager/event_class/confirm_delete.html'
    permission_required = 'event_class.delete'

    def delete(self, request, *args, **kwargs):
        success_url = self.get_success_url()
        try:
            self.get_object().delete()
            return HttpResponseRedirect(success_url)
        except ProtectedError:
            messages.info(
                request,
                'Невозможно удалить данный тип тренировок, т.к. '
                'существуют активные тренировки'
            )
            return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse('crm:manager:event-class:list')


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

    def get_clients_subscriptions(self, clients_qs):
        result = {}
        for client in clients_qs:
            client_subscriptions = result.setdefault(client, [])
            subs = client.clientsubscriptions_set.active_subscriptions_to_event(
                self.object
            )
            for sub in subs:
                client_subscriptions.append(sub)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Записанные клиенты. У них может и не быть абонементов
        signed_up_clients_qs = Client.objects.filter(
            id__in=self.object.attendance_set
            .filter(marked=False, signed_up=True)
            .order_by('name')
            .values_list('client', flat=True)
        )
        signed_up_clients = self.get_clients_subscriptions(signed_up_clients_qs)
        context['signed_up_clients_qs_count'] = signed_up_clients_qs.count()

        # Неотмеченные клиент. Они не записывались, но у них есть абонементы
        # которые позволяют сходить на это занятие
        unmarked_clients_qs = (
            Client.objects
            .with_active_subscription_to_event(self.object)
            .exclude(
                id__in=self.object
                .attendance_set
                .values_list('client', flat=True)
            )
            .order_by('name')
        )
        unmarked_clients = self.get_clients_subscriptions(unmarked_clients_qs)
        context['unmarked_clients_qs_count'] = unmarked_clients_qs.count()

        # Отмеченные клиенты. Они сходили на занятие и у них есть абонементы
        attendance_list_marked = (
            self.object.attendance_set
            .filter(marked=True)
            .select_related('client')
            .order_by('client__name')
        )
        context['attendance_list_marked_count'] = attendance_list_marked.count()

        selected_id = [
            x.id for x, _ in signed_up_clients.items()
        ]
        selected_id.extend([
            x.id for x, _ in unmarked_clients.items()
        ])
        selected_id.extend([
            x.client_id for x in attendance_list_marked
        ])

        rest_clients = Client.objects.exclude(id__in=selected_id)
        context['rest_clients_count'] = rest_clients.count()
        context['all_clients_count'] = (
            unmarked_clients_qs.count() + signed_up_clients_qs.count())
        self.object.save()

        context.update({
            'attendance_list_marked': attendance_list_marked,
            'signed_up_clients': signed_up_clients,
            'unmarked_clients': unmarked_clients,
            'sell_subscription_form': InplaceSellSubscriptionForm(
                subscription_type_qs=SubscriptionsType.objects.filter(
                    event_class=self.object.event_class)
            ),
            'max_start_subscription_date': self.object.date,
            'has_active_event_class': (
                EventClass.objects
                .active()
                .filter(id=self.object.event_class_id).exists()
            ),
            'rest_clients': rest_clients
        })

        context.update(
            event_class_id=self.kwargs.get('event_class_id'),
            event_year=self.kwargs.get('year'),
            event_month=self.kwargs.get('month'),
            event_day=self.kwargs.get('day'), )

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
        return reverse(
            'crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class SignUpClient(
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event.manipulate'

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.signup_for_event(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class SellAndMark(
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    CreateView
):
    """
    Sell subscription to client and sign up client for event.
    This view can work in two modes - as single page, and only as form processor
    Single page mode can be acquired by providing 'client_id' in kwargs,
    as form must know for which client we sell subscription.
    Form processor mode - work with form posted from other pages, and we assume
    that hidden client field will be populated with correct client_id
    There is no more difference with this two modes.

    By default if form was filled correct redirect will be on event page,
    but this behaviour can be changed if will be provided query string argument
    *scanner*. In this case redirected page will be scanner page for event.
    """
    form_class = InplaceSellSubscriptionForm
    template_name = 'crm/manager/event/sell-and-mark.html'
    permission_required = 'client_subscription.sale'

    def get(self, request, *args, **kwargs):
        # Prevent access to form page without client id.
        # In this case form is unusable
        if 'client_id' not in kwargs:
            return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if 'client_id' in self.kwargs:
            initial['client'] = self.kwargs['client_id']
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['subscription_type_qs'] = SubscriptionsType.objects.filter(
            event_class=self.get_object().event_class)
        return kwargs

    def get_success_url(self):
        self.kwargs.pop('client_id', None)
        if 'scanner' in self.request.GET:
            return reverse(
             'crm:manager:event-class:event:scanner', kwargs=self.kwargs)

        return reverse(
             'crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'client_id' in self.kwargs or \
                context['form'].cleaned_data['client']:
            if 'client_id' in self.kwargs:
                context['client'] = get_object_or_404(
                    Client, id=self.kwargs['client_id'])
            else:
                context['client'] = context['form'].cleaned_data['client']

        context['scanner'] = 'scanner' in self.request.GET
        context['event'] = self.get_object()
        context['form_back'] = self.get_success_url()
        return context

    def form_valid(self, form):
        cash_earned = form.cleaned_data['cash_earned']
        abon_price = form.cleaned_data['price']
        client = form.cleaned_data['client']
        default_reason = 'Покупка абонемента'
        current_user = self.request.user
        with transaction.atomic():
            client.add_balance_in_history(
                -abon_price, default_reason, changed_by=current_user)
            if cash_earned:
                default_reason = 'Перечесление средств за абонемент'
                client.add_balance_in_history(
                    abon_price, default_reason, changed_by=current_user)
            client.save()
            subscription = form.save()
            subscription.event = self.get_object()
            subscription.sold_by = current_user
            subscription.save()
            try:
                client.mark_visit(self.get_object(), subscription)
            except ValueError:
                messages.warning(
                    self.request,
                    'Не получилось отметить визит - возможно абонемент был '
                    'продан на будущую дату'
                )
            except ClientAttendanceExists:
                # Strange case - sell - it's ok, but existent attendance won't
                # be related with new subscription, as it exists
                pass
            enqueue('notify_client_buy_subscription', subscription.id)
        return HttpResponseRedirect(self.get_success_url())


class CancelAttendance(
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event.manipulate'

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        client_id = self.kwargs.pop('client_id')
        client = Client.objects.get(id=client_id)
        client.cancel_signup_for_event(event)
        self.url = self.get_success_url()
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class SignUpClientWithoutSubscription (
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    FormView
):
    form_class = SignUpClientMultiForm
    template_name = 'crm/manager/event/mark_client_without_sub.html'
    permission_required = 'event.manipulate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        context.update({
            'event': event,
        })
        return context

    def add_exists(self, form):
        clients = form.cleaned_data['client']
        event = self.get_object()
        for client in clients:
            client.signup_for_event(event)

    def add_new(self, form: ClientForm):
        event = self.get_object()
        client = form.save()
        client.signup_for_event(event)

    def form_valid(self, form):
        if form['exists'].is_valid() and "exists" in self.request.POST:
            self.add_exists(form['exists'])
        if form['new'].is_valid() and "new" in self.request.POST:
            self.add_new(form['new'])

        return super(SignUpClientWithoutSubscription, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'crm:manager:event-class:event:event-by-date', kwargs=self.kwargs)


class MarkClient (
    PermissionRequiredMixin,
    RevisionMixin,
    EventByDateMixin,
    RedirectView
):
    permission_required = 'event.manipulate'

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


class CreateEditEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, datetime.date):
            return o.strftime('%d.%m.%Y')
        elif isinstance(o, datetime.time):
            return o.strftime('%H:%M')

        return json.JSONEncoder.default(self, o)


class CreateEdit(
    PermissionRequiredMixin,
    RevisionMixin,
    TemplateView
):

    template_name = 'crm/manager/event_class/form.html'
    permission_required = 'event_class.add'
    object: Optional[EventClass] = ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None

    def get_object(self):
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(EventClass, pk=self.kwargs['pk'])

    def _time_to_js(self, time_str):
        try:
            return datetime.datetime.strptime(time_str, '%H:%M:%S')\
                .time().strftime('%H:%M')
        except ValueError:
            pass

        return datetime.datetime.strptime(time_str, '%H:%M')\
            .time().strftime('%H:%M')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'object': self.object,
            'coaches': Coach.objects.all(),
            'locations': Location.objects.all(),
            'select2js': settings.SELECT2_JS,
            'select2css': settings.SELECT2_CSS
        })

        if self.object:
            existing_sections = {
                x.id: {
                    'section_id': x.id,
                    'singular_event': x.singular_event,
                    'from_date': x.from_date,
                    'to_date': x.to_date,
                    'day_data': {
                        day_num: {
                            'day_num': day_num,
                            'from_time': self._time_to_js(data[0]),
                            'to_time': self._time_to_js(data[1])
                        } for day_num, data in x.day_data.items()
                    }
                } for x in self.object.eventclasssection_set.all()
            }
            context['existing_sections'] = json.dumps(
                existing_sections, cls=CreateEditEncoder)
            context['uidCounter'] = max(existing_sections.keys(), default=0) + 1
            try:
                one_time_sub = SubscriptionsType.objects.get(
                    one_time=True, event_class=self.object)
                context['one_time_price'] = one_time_sub.price
            except (
                SubscriptionsType.DoesNotExist,
                SubscriptionsType.MultipleObjectsReturned
            ):
                context['one_time_price'] = None
        else:
            context['uidCounter'] = 1
            context['existing_sections'] = json.dumps([])

            try:
                one_time_sub = SubscriptionsType.objects.get(
                    one_time=True, event_class=self.object)
                context['one_time_price'] = one_time_sub.price
            except (
                SubscriptionsType.DoesNotExist,
                SubscriptionsType.MultipleObjectsReturned
            ):
                context['one_time_price'] = None

        return context


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

    # Id of client, for which we will sell new subscription
    # Usable for case when client is marked to event, but don't have any
    # active subscription
    sell_to = None

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
        subscription = (
            ClientSubscriptions.objects
            .active_subscriptions_to_event(event)
            .filter(client=client)
            .order_by('purchase_date')
            .first()
        )
        if not subscription:
            # Change redirect behaviour, as we can sell subscription
            self.sell_to = client.id
            return

        try:
            subscription.mark_visit(event)
        except ClientAttendanceExists:
            messages.warning(self.request, f'{client} уже отмечен')
        else:
            messages.info(
                self.request, f'{client} отмечен по абонементу {subscription}')
            return

    def get_redirect_url(self, *args, **kwargs):
        kwargs.pop('code')
        # In case of activation of sell mode - add back argument
        if self.sell_to:
            kwargs['client_id'] = self.sell_to
            self.pattern_name = (
                'crm:manager:event-class:event:sell-and-mark-to-client'
            )
            url = super().get_redirect_url(*args, **kwargs) + '?scanner=True'
        else:
            url = super().get_redirect_url(*args, **kwargs)

        return url


class DoCloseEvent(
    PermissionRequiredMixin,
    EventByDateMixin,
    RedirectWithActionView
):
    permission_required = 'event.close'
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
    permission_required = 'event.open'
    pattern_name = 'crm:manager:event-class:event:event-by-date'

    def run_action(self):
        event = self.get_object()
        event.open_event()
        return


class CreateEventClass(CreateAPIView):
    serializer_class = EventClassEditSerializer


class UpdateEventClass(UpdateAPIView):
    serializer_class = EventClassEditSerializer
    queryset = EventClass.objects.all()
