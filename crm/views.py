from bootstrap_datepicker_plus import DatePickerInput
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django import forms
from crm.forms import ClientForm

from .models import Client, EventClass, SubscriptionsType, ClientSubscriptions


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

    def get_context_data(self, **kwargs):
        context = super(ClientsListView, self).get_context_data(**kwargs)
        context["clientsubscriptions"] = ClientSubscriptions.objects.all().order_by('id')
        context["subscriptions"] = SubscriptionsType.objects.all()
        return context


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
    fields = ['name', 'price',
              'duration', 'visit_limit']


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
    model = ClientSubscriptions
    fields = ['subscription',
              'purchase_date', 'start_date']

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.сlient.id])

    def get_context_data(self, **kwargs):
        self.client = Client.objects.get(id=self.kwargs['client_id'])
        kwargs['client'] = self.client
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        self.сlient = Client.objects.get(id=self.kwargs['client_id'])
        form.instance.client = self.сlient
        return super().form_valid(form)

class ClientSubscriptionUpdateView(UpdateView):
    model = ClientSubscriptions
    fields = ['subscription',
              'purchase_date', 'start_date']

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
