from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView,
)

from crm.forms import DayOfTheWeekClassForm, EventAttendanceForm, EventClassForm
from crm.models import Attendance, DayOfTheWeekClass, Event, EventClass
from crm.views.mixin import UserManagerMixin


class List(LoginRequiredMixin, UserManagerMixin, ListView):
    model = EventClass
    template_name = 'crm/manager/event_class/list.html'


class Delete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    model = EventClass
    success_url = reverse_lazy('crm:manager:event-class:list')
    template_name = 'crm/manager/event_class/confirm_delete.html'


class Calendar(LoginRequiredMixin, UserManagerMixin, DetailView):
    model = EventClass
    context_object_name = 'event_class'
    template_name = 'crm/manager/event_class/calendar.html'

    def get_context_data(self, **kwargs):
        # По умолчанию выводить календарь на 60 дней
        # от первого числа текущего месяца
        first_day = timezone.now().replace(day=1).date()
        context = super().get_context_data(**kwargs)
        context['events'] = self.get_object().get_calendar(
            first_day, first_day + timedelta(days=60)
        )
        return context


class EventByDate(LoginRequiredMixin, UserManagerMixin, DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'crm/manager/event/detail.html'

    def get_object(self, queryset=None):
        event_date = date(
            self.kwargs['year'], self.kwargs['month'], self.kwargs['day']
        )
        try:
            return Event.objects.get(
                event_class_id=self.kwargs['event_class_id'],
                date=event_date
            )
        except Event.DoesNotExist:
            event_class = get_object_or_404(
                EventClass, id=self.kwargs['event_class_id'])
            return Event(date=event_date, event_class=event_class)


class MarkEventAttendance(LoginRequiredMixin, UserManagerMixin, CreateView):
    template_name = 'crm/manager/client/add-attendance.html'
    form_class = EventAttendanceForm

    def get_object(self, queryset=None):
        event_date = date(
            self.kwargs['year'], self.kwargs['month'], self.kwargs['day']
        )
        event, _ = Event.objects.get_or_create(
            event_class_id=self.kwargs['event_class_id'],
            date=event_date)

        return Attendance(event=event)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.get_object()})
        return kwargs

    def get_success_url(self):
        return reverse(
            'crm:manager:event-class:event-by-date', kwargs=self.kwargs)


def eventclass_view(request, pk=None):
    # TODO: Refactor to CBV!!!
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
            # сохраняем или удаляем дни недели, которые уже
            # были у тренировки ранее
            if pk:
                for weekday in eventclass.dayoftheweekclass_set.all():
                    weekdayform = DayOfTheWeekClassForm(
                        request.POST,
                        prefix=f'weekday{weekday.day}',
                        instance=weekday)
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
                    weekdayform = DayOfTheWeekClassForm(
                        request.POST, prefix=f'weekday{i}', instance=weekday)
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
                weekdays[weekday.day] = DayOfTheWeekClassForm(
                    instance=weekday,
                    prefix=f'weekday{weekday.day}',
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
                weekdays[i] = DayOfTheWeekClassForm(
                    instance=weekday, prefix=f'weekday{weekday.day}')

    return render(
        request,
        'crm/manager/event_class/form.html',
        {
            'eventclass_form': eventclass_form,
            'weekdays': weekdays
        }
    )
