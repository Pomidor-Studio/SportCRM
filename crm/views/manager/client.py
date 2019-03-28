from typing import Optional

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, UpdateView,
)
from django_filters.views import FilterView
from django_multitenant.utils import get_current_tenant
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import DateField, IntegerField
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.enums import BALANCE_REASON
from crm.filters import ClientFilter
from crm.forms import (
    ClientForm, ClientSubscriptionForm, ExtendClientSubscriptionForm,
)
from crm.models import (
    Client, ClientSubscriptions, ExtensionHistory, SubscriptionsType,
    EventClass,
)
from crm.serializers import ClientSubscriptionCheckOverlappingSerializer

from google_tasks.tasks import enqueue


class List(PermissionRequiredMixin, FilterView):
    model = Client
    filterset_class = ClientFilter
    template_name = 'crm/manager/client/list.html'
    context_object_name = 'clients'
    paginate_by = 25
    permission_required = 'client'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['has_active_event_class'] = EventClass.objects.active().exists()
        context['vk_group_id'] = get_current_tenant().vk_group_id
        return context


class Create(PermissionRequiredMixin, RevisionMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/manager/client/form.html'
    permission_required = 'client.add'


class Update(PermissionRequiredMixin, RevisionMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/manager/client/form.html'
    permission_required = 'client.edit'


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = Client
    template_name = 'crm/manager/client/confirm_delete.html'
    success_url = reverse_lazy('crm:manager:client:list')
    permission_required = 'client.delete'


class Detail(PermissionRequiredMixin, DetailView):
    model = Client
    template_name = 'crm/manager/client/detail.html'
    permission_required = 'client'


class ClientMixin:
    def get_client(self) -> Client:
        return get_object_or_404(Client, id=self.kwargs['client_id'])


class AddSubscription(
    PermissionRequiredMixin,
    ClientMixin,
    RevisionMixin,
    CreateView
):
    form_class = ClientSubscriptionForm
    template_name = "crm/manager/client/add-subscriptions.html"
    permission_required = 'client_subscription.sale'

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.kwargs['client_id']])

    def get_initial(self):
        initial = super().get_initial()
        client = self.get_client()
        initial['client'] = client

        # Add preselected subscription type from previous client subscriptions
        # history.
        last_sub = client.last_sub()
        if last_sub:
            initial['subscription'] = last_sub.subscription
            initial['visits_left'] = last_sub.subscription.visit_limit
            initial['price'] = last_sub.subscription.price

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['allow_check_overlapping'] = True
        return context

    def form_valid(self, form):
        cash_earned = form.cleaned_data['cash_earned']
        abon_price = form.cleaned_data['price']
        client = self.get_client()

        with transaction.atomic():
            client.add_balance_in_history(
                -abon_price, BALANCE_REASON.BY_SUBSCRIPTION,
                skip_notification=True
            )
            if cash_earned:
                client.add_balance_in_history(
                    abon_price, BALANCE_REASON.UPDATE_BALANCE,
                    skip_notification=True
                )
            client.save()
            response = super().form_valid(form)
            enqueue('notify_client_buy_subscription', self.object.id)

        return response


class SubscriptionUpdate(
    PermissionRequiredMixin,
    RevisionMixin,
    UpdateView
):
    model = ClientSubscriptions
    form_class = ClientSubscriptionForm
    template_name = 'crm/manager/client/add-subscriptions.html'
    permission_required = 'client_subscription.edit'

    def activated_subscription(self):
        return self.object.attendance_set.exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['disable_subscription_type'] = True
        kwargs['activated_subscription'] = self.activated_subscription()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = ExtensionHistory.objects.filter(
            client_subscription=self.object.id)
        context['client'] = self.object.client
        context['activated_subscription'] = self.activated_subscription()
        context['allow_check_overlapping'] = False
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.activated_subscription():
            messages.warning(
                self.request,
                'По этому абонементу были посещения, по этому, его уже нельзя '
                'редактировать.'
            )
        return response


class AddSubscriptionWithExtending(AddSubscription):

    object: ClientSubscriptions = ...

    def form_valid(self, form):
        with transaction.atomic():
            ret_val = super().form_valid(form)

            to_cancel_events = self.object.canceled_events()[:len(
                self.object.remained_events()
            )]
            for event in to_cancel_events:
                self.object.extend_by_cancellation(event)
        return ret_val


class CheckOverlapping(RetrieveAPIView):
    serializer_class = ClientSubscriptionCheckOverlappingSerializer

    def get_object(self):
        subscription = SubscriptionsType.objects.get(
            id=self.request.query_params.get('st'))
        start_date = DateField(input_formats=['%d.%m.%Y']).to_internal_value(
            self.request.query_params.get('start'))
        visits_left = IntegerField().to_internal_value(
            self.request.query_params.get('vl'))

        return ClientSubscriptions(
            subscription=subscription,
            start_date=start_date,
            end_date=subscription.end_date(start_date),
            visits_left=visits_left
        )


class SubscriptionExtend(PermissionRequiredMixin, RevisionMixin, FormView):
    form_class = ExtendClientSubscriptionForm
    template_name = 'crm/manager/client/subscription_extend.html'
    permission_required = 'client_subscription.extend'

    object: ClientSubscriptions = ...

    def get_object(self):
        self.object = get_object_or_404(
            ClientSubscriptions, id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['subscription'] = self.object
        return kwargs

    def get(self, request, *args, **kwargs):
        self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object.extend_duration(
            form.cleaned_data['visit_limit'],
            form.cleaned_data['reason']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', kwargs={'pk': self.object.client_id})


class SubscriptionDelete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = ClientSubscriptions
    template_name = 'crm/manager/client/subscription_confirm_delete.html'
    permission_required = 'client_subscription.delete'

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.object.client.id])
