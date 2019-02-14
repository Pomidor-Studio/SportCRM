from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from ..forms import (
    AttendanceForm, ClientForm, ClientSubscriptionForm, DayOfTheWeekClassForm,
    EventAttendanceForm, EventClassForm, ExtendClientSubscriptionForm,
)
from ..models import (
    Attendance, Client, ClientSubscriptions, DayOfTheWeekClass, Event,
    EventClass, SubscriptionsType,
)


class ManagerHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/base.html'


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
    fields = '__all__'


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


def event_date_view(request, event_class_id:int, year:int, month:int, day:int):
    """Обработка событиея по типу и дате"""
    event_date = date(year, month, day)
    try:
        event = Event.objects.get(event_class_id=event_class_id, date=event_date)
    except Event.DoesNotExist:
        event_class = get_object_or_404(EventClass, pk=event_class_id)
        event = Event(date=event_date, event_class=event_class)
    return render(request, 'crm/event_detail.html', {
        'event': event})


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


def event_mark_view(request, event_class_id:int, year:int, month:int, day:int):
    """Отметить посещение по событию"""
    if request.method == "POST":
        event_date = date(year, month, day)
        # получаем требуемое события, если нет такого, то создаем
        event = Event.objects.get_or_create(event_class_id=event_class_id, date=event_date)[0]

        # создаем посещение
        attendance = Attendance(event=event)
        # дополняем модель данными из формы
        attendance_form = EventAttendanceForm(request.POST, instance=attendance)
        if attendance_form.is_valid():
            attendance_form.save()
        return HttpResponseRedirect(reverse('crm:class-event-date', kwargs={'event_class_id': event_class_id,
                                                       'year': year,
                                                       'month': month,
                                                       'day': day}))
    else:
        return render(request, 'crm/attendance_form.html', {
                      'form': EventAttendanceForm()})


def eventclass_view(request, pk=None):
    """редактирование типа события"""
    # инициализируем служебный массив 7 пустыми элементами
    weekdays = [None] * 7
    if request.method == "POST":
        if pk:
            eventclass = get_object_or_404(EventClass, pk=pk)
        else:
            eventclass = None
        eventclass_form = EventClassForm(request.POST, instance=eventclass)
        eventclass = eventclass_form.save()
        with transaction.atomic():
            # сохраняем или удаляем дни недели, которые уже были у тренировки ранее
            if pk:
                for weekday in eventclass.dayoftheweekclass_set.all():
                    weekdayform = DayOfTheWeekClassForm(request.POST, prefix='weekday'+str(weekday.day), instance=weekday)
                    if weekdayform.is_valid():
                        if weekdayform.cleaned_data['checked']:
                            weekdayform.save()
                        else:
                            weekday.delete()
                    weekdays[weekday.day] = weekdayform

            # Проверяем все остальные дни
            for i in range(7):
                if not weekdays[i]:
                    weekday = DayOfTheWeekClass(day=i)
                    weekdayform = DayOfTheWeekClassForm(request.POST, prefix='weekday' + str(i), instance=weekday)
                    if weekdayform.is_valid():
                        if weekdayform.cleaned_data['checked']:
                            weekdayform.instance.event = eventclass
                            weekdayform.save()
                    weekdays[i] = weekdayform

    else:
        if pk:
            eventclass = get_object_or_404(EventClass, pk=pk)
            # заполняем формы по сохраненным дням
            for weekday in eventclass.dayoftheweekclass_set.all():
                weekdays[weekday.day] = DayOfTheWeekClassForm(instance=weekday,
                                                              prefix='weekday' + str(weekday.day),
                                                              initial={'checked': True})
        else:
            eventclass = None

        eventclass_form = EventClassForm(instance=eventclass)

        # Заполняем форму по всем остальным дням
        for i in range(7):
            if not weekdays[i]:
                weekday = DayOfTheWeekClass()
                weekday.event = eventclass
                weekday.day = i
                weekdays[i] = DayOfTheWeekClassForm(instance=weekday, prefix='weekday'+str(weekday.day))

    return render(request, 'crm/eventclass_form.html', {
                  'eventclass_form':eventclass_form,
                  'weekdays':weekdays})


def eventcalendar(request, pk: int ):
    """Календарь одной тренеровки"""
    event_class:EventClass = get_object_or_404(EventClass, pk=pk)
    events = event_class.get_calendar(date(2019,1,1), date(2019,3,1))
    return render(request, 'crm/eventcalendar.html', {
        'event_class': event_class,
        'events': events})

