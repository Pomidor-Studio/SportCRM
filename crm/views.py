from bootstrap_datepicker_plus import DatePickerInput
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django import forms

from .forms import (ClientForm,
                    ClientSubscriptionForm,
                    AttendanceForm,
                    ExtendClientSubscriptionForm,
                    EventClassForm,
                    EventAttendanceForm)

from .models import (Client,
                     EventClass,
                     SubscriptionsType,
                     ClientSubscriptions,
                     Attendance,
                     Event,
                     DayOfTheWeekClass,
                     )


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

    def get_queryset(self):
        name_query = self.request.GET.get('client')
        if name_query:
            clients_list = Client.objects.filter(name__icontains=name_query)
        else:
            clients_list = Client.objects.all()
        return clients_list


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


def ExtendSubscription(request, pk=None):
    if request.method == 'POST':
        print(request.POST)
        ClientSubscriptions.objects.get(pk=request.POST['object_id']).extend_duration(request.POST['visit_limit'])
        return HttpResponseRedirect(reverse('crm:client-detail', args=[request.POST['client_id']]))
    else:
        subscription = ClientSubscriptions.objects.get(pk=pk)
        form = ExtendClientSubscriptionForm(subscription=subscription)
    return render(request, 'crm/extend_subscription.html', {'form': form})


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


class ClientSubscriptionDeleteView(DeleteView):
    model = ClientSubscriptions

    def get_success_url(self):
        return reverse('crm:client-detail', args=[self.object.client.id, ])


class EventClassList(ListView):
    model = EventClass


class EventClassCreate(CreateView):
    model = EventClass
    form_class = EventClassForm


class EventClassUpdate(UpdateView):
    model = EventClass
    form_class = EventClassForm


class EventClassDelete(DeleteView):
    model = EventClass
    success_url = reverse_lazy('crm:eventclass_list')


class AttendanceCreateView(CreateView):
    model = Attendance
    form_class = AttendanceForm

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


class EventList(ListView):
    # template_name = 'polls/bars.html'
    # context_object_name = 'latest_question_list'
    model = Event


class EventCreateView(CreateView):
    model = Event
    fields = '__all__'

    def get_success_url(self):
        return reverse('crm:event-list')


class EventUpdateView(UpdateView):
    model = Event
    fields = '__all__'

    def get_success_url(self):
        return reverse('crm:event-list')


class EventDeleteView(DeleteView):
    model = Event
    template_name = "crm/common_confirm_delete.html"

    def get_success_url(self):
        return reverse('crm:event-list')


class EventDetailView(DetailView):
    model = Event
    context_object_name = 'event'


class EventAttendanceCreateView(CreateView):
    model = Attendance
    form_class = EventAttendanceForm

    def get_initial(self):
        initial = super(EventAttendanceCreateView, self).get_initial()
        event = get_object_or_404(Event, pk=self.kwargs.get('event_id'))
        initial['event'] = event
        return initial

    # def form_valid(self, form):
    #     form.instance.event_id = self.kwargs['event_id']
    #     return super(EventAttendanceCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('crm:event-detail', args=[self.kwargs['event_id']])
