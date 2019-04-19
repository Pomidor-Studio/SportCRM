from django import forms
from django.conf.locale.ru.formats import DATE_INPUT_FORMATS
from django.urls import reverse_lazy
from django.views.generic import DeleteView, UpdateView
from django_filters.views import FilterView
from rest_framework.generics import RetrieveAPIView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.filters import SubscriptionsTypeFilterSet
from crm.forms import SubscriptionsTypeForm
from crm.models import SubscriptionsType
from crm.serializers import SubscriptionRangeSerializer
from crm.views.mixin import CreateAndAddView, UnDeleteView


class List(PermissionRequiredMixin, FilterView):
    model = SubscriptionsType
    template_name = 'crm/manager/subscription/list.html'
    context_object_name = 'subscriptions'
    ordering = ['id']
    filterset_class = SubscriptionsTypeFilterSet
    permission_required = 'subscription'


class Create(PermissionRequiredMixin, RevisionMixin, CreateAndAddView):
    model = SubscriptionsType
    form_class = SubscriptionsTypeForm
    template_name = 'crm/manager/subscription/form.html'
    permission_required = 'subscription.add'
    add_another_url = 'crm:manager:subscription:new'
    message_info = 'Абонемент успешно создан'


class Update(PermissionRequiredMixin, RevisionMixin, UpdateView):
    permission_required = 'subscription.edit'
    model = SubscriptionsType
    form_class = SubscriptionsTypeForm
    template_name = 'crm/manager/subscription/form.html'


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_delete.html'
    permission_required = 'subscription.delete'


class UnDelete(PermissionRequiredMixin, RevisionMixin, UnDeleteView):
    model = SubscriptionsType
    success_url = reverse_lazy('crm:manager:subscription:list')
    template_name = 'crm/manager/subscription/confirm_undelete.html'
    permission_required = 'subscription.undelete'


class SellRange(RetrieveAPIView):
    serializer_class = SubscriptionRangeSerializer
    queryset = SubscriptionsType

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['requested_date'] = forms.DateField(
            input_formats=DATE_INPUT_FORMATS).to_python(
            self.request.query_params['requested_date'])
        return context




