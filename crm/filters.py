from copy import copy

import django_filters
from django import forms
from django.http import QueryDict

from crm import models


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        label='Искать по ФИО',
        lookup_expr='icontains'
    )

    class Meta:
        model = models.Client
        fields = ('name',)


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
