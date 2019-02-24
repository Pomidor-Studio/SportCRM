from datetime import date, timedelta
from typing import List, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView,
    TemplateView,
)

from crm.forms import DayOfTheWeekClassForm, EventAttendanceForm, EventClassForm
from crm.models import Attendance, DayOfTheWeekClass, Event, EventClass, Client
from crm.views.mixin import UserManagerMixin


class ObjList(LoginRequiredMixin, UserManagerMixin, ListView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attendance_list = self.object.attendance_set.all().select_related('client').order_by('client__name')
        context.update({
            'attendance_list': attendance_list,
            'clients': Client.objects.exclude(id__in=[x.client_id for x in attendance_list])
        })

        return context

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
        return reverse('crm:manager:event-class:event-by-date', kwargs=self.kwargs)


class CreateEdit(LoginRequiredMixin, UserManagerMixin, TemplateView):

    template_name = 'crm/manager/event_class/form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None
        self.weekdays: List[Optional[DayOfTheWeekClassForm]] = [None] * 7
        self.form: EventClassForm = None

    def get_object(self):
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(EventClass, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'eventclass_form': self.form,
            'weekdays': self.weekdays
        })
        return context

    def get(self, request, *args, **kwargs):
        self.get_object()
        prefiled_days = {}
        if self.object:
            # Получаем уже записанные дни для тип тренировки
            prefiled_days = {
                x.day: x for x in self.object.dayoftheweekclass_set.all()
            }

        self.form = EventClassForm(instance=self.object)

        # Заполняем форму дней тренировки
        for i in range(7):
            sub_form_obj = prefiled_days.get(
                i, DayOfTheWeekClass(event=self.object, day=i))
            self.weekdays[i] = DayOfTheWeekClassForm(
                instance=sub_form_obj,
                prefix=f'weekday{i}',
                initial={'checked': bool(sub_form_obj.id)}
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_object()

        self.form = EventClassForm(request.POST, instance=self.object)
        with transaction.atomic():
            self.object = self.form.save()

            # сохраняем или удаляем дни недели, которые уже
            # были у тренировки ранее
            for weekday in self.object.dayoftheweekclass_set.all():
                weekdayform = DayOfTheWeekClassForm(
                    request.POST,
                    prefix=f'weekday{weekday.day}',
                    instance=weekday)
                if weekdayform.is_valid():
                    if weekdayform.cleaned_data['checked']:
                        weekdayform.save()
                    else:
                        weekday.delete()
                self.weekdays[weekday.day] = weekdayform

            # Проверяем все остальные дни
            for i in range(7):
                if not self.weekdays[i]:
                    weekday = DayOfTheWeekClass(day=i)
                    weekdayform = DayOfTheWeekClassForm(
                        request.POST, prefix=f'weekday{i}', instance=weekday)
                    if weekdayform.is_valid():
                        if weekdayform.cleaned_data['checked']:
                            weekdayform.instance.event = self.object
                            weekdayform.save()
                    self.weekdays[i] = weekdayform

        return HttpResponseRedirect(reverse(
            'crm:manager:event-class:update', kwargs={'pk': self.object.id}))
