from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from crm.forms import AttendanceForm, ClientForm, ClientSubscriptionForm
from crm.models import Attendance, Client
from crm.views.mixin import UserManagerMixin


class List(LoginRequiredMixin, UserManagerMixin, ListView):
    model = Client
    template_name = 'crm/manager/client/list.html'
    context_object_name = 'clients'

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
