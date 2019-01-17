from bootstrap_datepicker_plus import DatePickerInput
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django import forms

from .models import Client, EventClass, SubscriptionsType, ClientSubscriptions


def home(request):
    return render(request, 'crm/home.html')


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

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        template_name = 'crm/client_form.html'
        fields = ['name', 'address',
                  'birthday', 'phone_number', 'email_address']
        labels = {
            'name':'Имя',
            'address':'Адрес',
            'birthday':'Дата рождения',
            'phone_number':'Номер телефона',
            'email_address':'Электронный адрес',
        }
        widgets = {
            'birthday': DatePickerInput()
        }

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
    fields = ['name', 'address',
              'birthday', 'phone_number', 'email_address']


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
        return reverse('crm:client_detail', args=[self.client.id])

    def get_context_data(self, **kwargs):
        self.country = get_object_or_404(Client, id=self.kwargs['client_id'])
        kwargs['client'] = self.client
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        self.country = get_object_or_404(Client, id=self.kwargs['client_id'])
        form.instance.client = self.Client
        return super().form_valid(form)

class EventClassList(ListView):
    # template_name = 'polls/index.html'
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
