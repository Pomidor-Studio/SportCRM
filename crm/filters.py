from copy import copy

import django_filters
from bootstrap_datepicker_plus import DatePickerInput
from django import forms
from django.http import QueryDict

from crm import models
from crm.models import Coach, EventClass, Event


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        label='Искать по ФИО',
        lookup_expr='icontains'
    )

    class Meta:
        model = models.Client
        fields = ('name',)


class EventReportFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(label='Дата с:',
        widget=DatePickerInput(format='%d.%m.%Y',
                                         attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}))
    date_to = django_filters.DateFilter(label='Дата по:',
        widget=DatePickerInput(format='%d.%m.%Y',
                                         attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}))
    coach = django_filters.ModelChoiceFilter(
        label='Тренер:',
        queryset=Coach.objects.all(),
    )
    event_class = django_filters.ModelChoiceFilter(
        label='Тренировка:',
        queryset=EventClass.objects.all(),
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        new_data = data.copy() if data is not None else QueryDict(mutable=True)
        print(new_data.get('date_from'))
        # filter param is either missing or empty
        date_from = new_data.get('date_from')
        date_to = new_data.get('date_to')
        coach =  new_data.get('coach')
        event_class = new_data.get('event_class')

        new_data['date_from'] = date_from
        new_data['date_to'] = date_to
        new_data['coach'] = coach
        new_data['event_class'] = event_class

        super().__init__(new_data, queryset, request=request, prefix=prefix)

        self.queryset = (
            Event.objects.all()
        )

        print(self.queryset)



class ArchivableFilterSet(django_filters.FilterSet):
    with_archive = django_filters.BooleanFilter(
        method='filter_with_archive'
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        new_data = data.copy() if data is not None else QueryDict(mutable=True)

        # filter param is either missing or empty
        with_archive = forms.BooleanField().to_python(
            new_data.get('with_archive')
        )
        new_data['with_archive'] = with_archive

        super().__init__(new_data, queryset, request=request, prefix=prefix)

        self.queryset = (
            self._meta.model.all_objects.all()
            if with_archive else
            self._meta.model.objects.all()
        )

    @property
    def toggled_data(self):
        new_data = self.data.copy()
        new_data['with_archive'] = not new_data['with_archive']
        return new_data

    def filter_with_archive(self, queryset, name, value):
        """
        Filtering was done during class initialization
        """
        return queryset


class CoachFilter(ArchivableFilterSet):
    class Meta:
        model = models.Coach
        fields = '__all__'


class LocationFilter(ArchivableFilterSet):
    class Meta:
        model = models.Location
        fields = '__all__'


class SubscriptionsTypeFilterSet(ArchivableFilterSet):
    class Meta:
        model = models.SubscriptionsType
        fields = '__all__'
