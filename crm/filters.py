from datetime import datetime, timedelta, date

import django_filters
from dateutil.relativedelta import relativedelta
from django import forms
from django.forms.utils import ErrorList
from django.http import QueryDict
from django.utils import dateformat
from phonenumber_field import modelfields

from crm import models
from crm.utils import BootstrapDateFromToRangeFilter


class EventReportFilter(django_filters.FilterSet):
    date = BootstrapDateFromToRangeFilter(label='Диапазон дат:')
    coach = django_filters.ModelMultipleChoiceFilter(
        label='Тренер:',
        field_name='event_class__coach',
        queryset=models.Coach.objects,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'selectpicker form-control',
                'multiple': '',
                'data-selected-text-format': 'static',
                'title': 'Тренер',
            }
        ),
        required=False,
    )
    event_class = django_filters.ModelMultipleChoiceFilter(
        label='Тип тренировки:',
        field_name='event_class',
        queryset=models.EventClass.objects,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'selectpicker form-control',
                'multiple': '',
                'data-selected-text-format': 'static',
                'title': 'Тип тренировки',
            }
        ),
        required=False,
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        with_defaults_data = (
            data.copy() if data is not None else QueryDict(mutable=True)
        )
        # Подставляем текущий месяц
        if data is None or not ('date_after' in data and 'date_before' in data):
            with_defaults_data['date_after'] = dateformat.format(
                datetime.today().replace(day=1), 'd.m.Y'
            )
            with_defaults_data['date_before'] = dateformat.format(
                datetime.today().replace(day=1) + relativedelta(months=1) - timedelta(days=1),
                'd.m.Y'
            )
        super().__init__(
            with_defaults_data, queryset, request=request, prefix=prefix)

    class Meta:
        model = models.Event
        fields = ('date',)


class VisitReportFilter(forms.Form):
    event_class = forms.ModelChoiceField(
        label='Тип тренировки:',
        queryset=models.EventClass.objects,
        empty_label=None,
        widget=forms.Select(
            attrs={
                'class': 'selectpicker form-control',
            }
        ),
    )
    month = forms.ChoiceField(
        label='Месяц:',
        choices=(
            (1, 'Январь'),
            (2, 'Февраль'),
            (3, 'Март'),
            (4, 'Апрель'),
            (5, 'Май'),
            (6, 'Июнь'),
            (7, 'Июль'),
            (8, 'Август'),
            (9, 'Сентябрь'),
            (10, 'Октябрь'),
            (11, 'Ноябрь'),
            (12, 'Декабрь'),
        ),
        widget=forms.Select(
            attrs={
                'class': 'selectpicker form-control',
                'title': 'Месяц',
            }
        ),
    )
    year = forms.ChoiceField(
        label='Год:',
        choices=(
            (y, y) for y in range(2019, date.today().year + 1)
        ),
        widget=forms.Select(
            attrs={
                'class': 'selectpicker form-control',
                'title': 'Год',
            }
        ),
    )


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
            self._meta.model.all_objects
            if with_archive else
            self._meta.model.objects
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


class ManagerFilter(ArchivableFilterSet):
    class Meta:
        model = models.Manager
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


class ClientFilter(ArchivableFilterSet):
    name = django_filters.CharFilter(
        label='Искать по ФИО',
        lookup_expr='icontains'
    )
    debtor = django_filters.BooleanFilter(field_name='debtor', method='filter_debtor')
    long_time_not_go = django_filters.BooleanFilter(field_name='long_time_not_go', method='filter_long_time_not_go')

    def filter_debtor(self, queryset, name, value):
        return queryset.filter(balance__lt=0)

    def filter_long_time_not_go(self, queryset, name, value):
        long_time_not_go_ids = []
        month_ago = date.today() - relativedelta(months=1)

        for client in queryset.filter(
            clientsubscriptions__end_date__lt=month_ago
        ):
            last_sub = client.last_sub()
            if not last_sub:
                continue
            if last_sub.end_date < month_ago:
                long_time_not_go_ids.append(client.id)

        return queryset.filter(id__in=long_time_not_go_ids)

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)

    class Meta:
        model = models.Client
        fields = ('name', 'debtor',)
