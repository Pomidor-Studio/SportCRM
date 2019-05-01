from datetime import datetime, timedelta

import django_filters
from dateutil.relativedelta import relativedelta
from django import forms
from django.forms.utils import ErrorList
from django.http import QueryDict
from django_select2.forms import Select2MultipleWidget
from phonenumber_field import modelfields

from crm import models
from crm.utils import BootstrapDateRangeField


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        label='Искать по ФИО',
        lookup_expr='icontains'
    )
    debtor = django_filters.BooleanFilter(field_name='debtor', method='filter_debtor')

    def filter_debtor(self, queryset, name, value):
        return queryset.filter(balance__lt=0)

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)

    class Meta:
        model = models.Client
        fields = ('name', 'debtor',)


class EventReportFilter(forms.Form):
    date = BootstrapDateRangeField(
        label='Диапазон дат:',
    )
    employee = forms.ModelMultipleChoiceField(
        label='Сотрудник:',
        queryset=models.User.objects.all(),
        widget=Select2MultipleWidget,
        required=False,
    )
    event_class = forms.ModelMultipleChoiceField(
        label='Тип тренировки:',
        queryset=models.EventClass.objects.all(),
        widget=Select2MultipleWidget,
        required=False,
    )

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, field_order=None, use_required_attribute=None,
                 renderer=None):
        with_defaults_data = (
            data.copy() if data is not None else QueryDict(mutable=True)
        )
        # Подставляем текущий месяц
        if data is None or not ('date_after' in data and 'date_before' in data):
            with_defaults_data['date_after'] = datetime.today().replace(day=1)
            with_defaults_data['date_before'] = (
                datetime.today().replace(day=1) +
                relativedelta(months=1) - timedelta(days=1)
            )
        super().__init__(with_defaults_data, files, auto_id, prefix, initial, error_class, label_suffix,
                         empty_permitted, field_order,
                         use_required_attribute, renderer)


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
        filter_overrides = {
            modelfields.PhoneNumberField: {
                'filter_class': django_filters.CharFilter
            }
        }


class LocationFilter(ArchivableFilterSet):
    class Meta:
        model = models.Location
        fields = '__all__'


class SubscriptionsTypeFilterSet(ArchivableFilterSet):
    class Meta:
        model = models.SubscriptionsType
        fields = '__all__'

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.queryset = self.queryset.filter(one_time=False)
