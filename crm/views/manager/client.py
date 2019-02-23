from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, UpdateView,
)
from django_filters.views import FilterView
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import ClientFilter
from crm.forms import (
    AttendanceForm, ClientForm, ClientSubscriptionForm,
    ExtendClientSubscriptionForm,
)
from crm.models import Attendance, Client, ClientSubscriptions, ExtensionHistory
from crm.views.mixin import UserManagerMixin


class List(PermissionRequiredMixin, FilterView):
    model = Client
    filterset_class = ClientFilter
    template_name = 'crm/manager/client/list.html'
    context_object_name = 'clients'
    paginate_by = 25
    permission_required = 'client'


class Create(PermissionRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/manager/client/form.html'
    permission_required = 'client.add'


class Update(PermissionRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/manager/client/form.html'
    permission_required = 'client.edit'


class Delete(PermissionRequiredMixin, DeleteView):
    model = Client
    template_name = 'crm/manager/client/confirm_delete.html'
    success_url = reverse_lazy('crm:manager:client:list')
    permission_required = 'client.delete'


class Detail(PermissionRequiredMixin, DetailView):
    model = Client
    template_name = 'crm/manager/client/detail.html'
    permission_required = 'client'


class AddSubscription(PermissionRequiredMixin, CreateView):
    form_class = ClientSubscriptionForm
    template_name = "crm/manager/client/add-subscriptions.html"
    permission_required = 'is_manager'

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.kwargs['client_id']])

    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        return super().form_valid(form)


class AddAttendance(PermissionRequiredMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "crm/manager/client/add-attendance.html"
    permission_required = 'is_manager'

    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.kwargs['client_id']])


class SubscriptionExtend(PermissionRequiredMixin, FormView):
    form_class = ExtendClientSubscriptionForm
    template_name = 'crm/manager/client/subscription_extend.html'
    permission_required = 'is_manager'

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
            form['visit_limit'].data,
            form['reason'].data
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', kwargs={'pk': self.object.client_id})


class SubscriptionUpdate(PermissionRequiredMixin, UpdateView):
    model = ClientSubscriptions
    form_class = ClientSubscriptionForm
    template_name = 'crm/manager/client/add-subscriptions.html'
    permission_required = 'is_manager'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = ExtensionHistory.objects.filter(
            client_subscription=self.object.id)
        return context


class SubscriptionDelete(PermissionRequiredMixin, DeleteView):
    model = ClientSubscriptions
    template_name = 'crm/manager/client/subscription_confirm_delete.html'
    permission_required = 'is_manager'

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.object.client.id])
