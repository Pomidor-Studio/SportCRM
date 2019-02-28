from datetime import datetime, timedelta

import django_filters
# from bootstrap_datepicker_plus import DatePickerInput
from dateutil.relativedelta import relativedelta
from django import forms
from django.http import QueryDict
from django_select2.forms import Select2MultipleWidget, ModelSelect2MultipleWidget, Select2Widget, Select2TagWidget, \
    Select2TagMixin

from crm import models
from crm.utils import BootstrapDateFromToRangeFilter


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        label='Искать по ФИО',
        lookup_expr='icontains'
    )

    class Meta:
        model = models.Client
        fields = ('name',)


class EventReportFilter(django_filters.FilterSet):
    date = BootstrapDateFromToRangeFilter(label='Диапазон дат:', field_name='date')

    # date = django_filters.DateFromToRangeFilter(field_name='date')
    coach = django_filters.ModelMultipleChoiceFilter(
        label='Тренер:',
        field_name='event_class__coach',
        queryset=models.Coach.objects.all(),
        widget=Select2MultipleWidget
    )
    event_class = django_filters.ModelMultipleChoiceFilter(
        label='Тип тренировки:',
        field_name='event_class',
        queryset=models.EventClass.objects.all(),
        widget=Select2MultipleWidget
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        initial_data = data.copy() if data is not None else QueryDict(mutable=True)
        # Подставляем текущий месяц
        if data is None:
            initial_data['date_after'] = datetime.today().replace(day=1)
            initial_data['date_before'] = datetime.today().replace(day=1) + relativedelta(months=1) - timedelta(days=1)

        super().__init__(initial_data , queryset, request=request, prefix=prefix)
        #self.form['date'].initial = ['27.02.2019', '27.02.2019']



    class Meta:
        model = models.Event
        fields = ('date',)


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
