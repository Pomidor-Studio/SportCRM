from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, UpdateView,
)

from crm.forms import (
    AttendanceForm, ClientForm, ClientSubscriptionForm,
    ExtendClientSubscriptionForm,
)
from crm.models import Attendance, Client, ClientSubscriptions, ExtensionHistory
from crm.views.mixin import UserManagerMixin


class List(LoginRequiredMixin, UserManagerMixin, ListView):
    model = Client
    template_name = 'crm/manager/client/list.html'
    context_object_name = 'clients'
    paginate_by = 25

    def get_queryset(self):
        name_query = self.request.GET.get('client')
        if name_query:
            clients_list = Client.objects.filter(name__icontains=name_query)
        else:
            clients_list = Client.objects.all()
        return clients_list


class Create(LoginRequiredMixin, UserManagerMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/manager/client/form.html'


class Update(LoginRequiredMixin, UserManagerMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/manager/client/form.html'


class Delete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    model = Client
    template_name = 'crm/manager/client/confirm_delete.html'
    success_url = reverse_lazy('crm:manager:client:list')


class Detail(LoginRequiredMixin, UserManagerMixin, DetailView):
    model = Client
    template_name = 'crm/manager/client/detail.html'


class AddSubscription(LoginRequiredMixin, UserManagerMixin, CreateView):
    form_class = ClientSubscriptionForm
    template_name = "crm/manager/client/add-subscriptions.html"

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.kwargs['client_id']])

    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        return super().form_valid(form)


class AddAttendance(LoginRequiredMixin, UserManagerMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "crm/manager/client/add-attendance.html"

    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.kwargs['client_id']])


class SubscriptionExtend(LoginRequiredMixin, UserManagerMixin, FormView):
    form_class = ExtendClientSubscriptionForm
    template_name = 'crm/manager/client/subscription_extend.html'
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


class SubscriptionUpdate(LoginRequiredMixin, UserManagerMixin, UpdateView):
    model = ClientSubscriptions
    form_class = ClientSubscriptionForm
    template_name = 'crm/manager/client/add-subscriptions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = ExtensionHistory.objects.filter(
            client_subscription=self.object.id)
        return context


class SubscriptionDelete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    model = ClientSubscriptions
    template_name = 'crm/manager/client/subscription_confirm_delete.html'

    def get_success_url(self):
        return reverse(
            'crm:manager:client:detail', args=[self.object.client.id])
