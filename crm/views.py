from bootstrap_datepicker_plus import DatePickerInput
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django import forms
from .forms import ClientForm, ClientSubscriptionForm, AttendanceForm

from .models import Client, EventClass, SubscriptionsType, ClientSubscriptions, Attendance


def base(request):
    return render(request, 'crm/base.html')


def clientsv(request):
    context = {
        'clients': Client.objects.all(),
        'subscriptions': SubscriptionsType.objects.all(),
        'client_subscriptions': ClientSubscriptions.objects.all()
    }
    return render(request, 'crm/clients.html', context)


def subscriptionsv(request):
    context = {
        'subscriptions': Client.objects.all()
    }
    return render(request, 'crm/subscriptions.html', context)


class ClientsListView(ListView):
    model = Client
    template_name = 'crm/clients.html'
    context_object_name = 'clients'


class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm


class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm


class ClientDeleteView(DeleteView):
    model = Client
    success_url = '/clients'


class ClientDetailView(DetailView):
    model = Client
    context_object_name = 'clients'

    def get_context_data(self, **kwargs):
        context = super(ClientDetailView, self).get_context_data(**kwargs)
        context["clientsubscriptions"] = ClientSubscriptions.objects.all().order_by('id')
        context["subscriptions"] = SubscriptionsType.objects.all()
        return context


class SubscriptionsListView(ListView):
    model = SubscriptionsType
    template_name = 'crm/subscriptions.html'
    context_object_name = 'subscriptions'
    ordering = ['id']


class SubscriptionCreateView(CreateView):
    model = SubscriptionsType
    fields = '__all__'


class SubscriptionUpdateView(UpdateView):
    model = SubscriptionsType
    fields = ['name', 'price',
              'duration', 'visit_limit']


class SubscriptionDeleteView(DeleteView):
    model = SubscriptionsType
    success_url = '/subscriptions'


class SubscriptionDetailView(DetailView):
    model = SubscriptionsType


class ClientSubscriptionCreateView(CreateView):
    form_class = ClientSubscriptionForm
    template_name = "crm/clientsubscriptions_form.html"

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.kwargs['client_id']])

    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        return super(ClientSubscriptionCreateView, self).form_valid(form)


class ClientSubscriptionUpdateView(UpdateView):
    model = ClientSubscriptions
    form_class = ClientSubscriptionForm


class EventClassList(ListView):
    # template_name = 'polls/bars.html'
    # context_object_name = 'latest_question_list'
    model = EventClass


class EventClassCreate(CreateView):
    model = EventClass
    fields = '__all__'


class EventClassUpdate(UpdateView):
    model = EventClass
    fields = '__all__'


class EventClassDelete(DeleteView):
    model = EventClass
    success_url = reverse_lazy('crm:eventclass_list')


class AttendanceCreateView(CreateView):
    model = Attendance
    form_class = AttendanceForm
    # def get_context_data(self, **kwargs):
    #     context = super(AttendanceCreateView, self).get_context_data(**kwargs)
    #     context['client_id'] = self.kwargs['client_id']
    #     return context

    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        return super(AttendanceCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.kwargs['client_id']])


class AttendanceDelete(DeleteView):
    model = Attendance
    template_name = "crm/common_confirm_delete.html"

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.object.client_id, ])


