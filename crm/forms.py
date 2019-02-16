import calendar

from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from betterforms.multiform import MultiModelForm

from .models import (
    Attendance, Client, ClientSubscriptions, Coach, DayOfTheWeekClass,
    EventClass, SubscriptionsType,
)


from django_multitenant.utils import get_current_tenant


class TenantModelForm(forms.ModelForm):
    """Base from for multitenant"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # никакой универсальности, просто удаляем поле company если оно есть.
        if "company" in self.fields:
            del self.fields["company"]
        tenant = get_current_tenant()
        if tenant:
            for field in self.fields.values():

                if isinstance(field, (forms.ModelChoiceField, forms.ModelMultipleChoiceField,)):
                    # Check if the model being used for the ModelChoiceField has a tenant model field
                    if hasattr(field.queryset.model, 'tenant_id'):
                        # Add filter restricting queryset to values to this tenant only.
                        kwargs = {field.queryset.model.tenant_id: tenant}
                        field.queryset = field.queryset.filter(**kwargs)


class ClientForm(TenantModelForm):
    class Meta:
        model = Client

        fields = ['name', 'address',
                  'birthday', 'phone_number', 'email_address', 'vk_user_id']
        widgets = {
            'birthday': DatePickerInput(format='%d.%m.%Y',
                                        attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}),
            'address': forms.TextInput(attrs={"class": "form-control", "placeholder": "Адрес проживания"}),
            'name': forms.TextInput(attrs={"class": "form-control", "placeholder": "ФИО"}),
            'phone_number': forms.TextInput(attrs={"class": "form-control", "placeholder": "Номер телефона"}),
            'email_address': forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@email.com"}),
            'vk_user_id': forms.HiddenInput(),

        }


class DataAttributesSelect(forms.Select):

    def __init__(self, attrs=None, choices=(), data={}):
        super(DataAttributesSelect, self).__init__(attrs, choices)
        self.data = data

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super(DataAttributesSelect, self).create_option(name, value, label, selected, index, subindex=None,
                                                                 attrs=None)
        for data_attr, values in self.data.items():
            option['attrs'][data_attr] = values[option['value']]

        return option


class ExtendClientSubscriptionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.subscription = kwargs.pop('subscription')
        super(ExtendClientSubscriptionForm, self).__init__(*args, **kwargs)
        self.fields['visit_limit'].initial = self.subscription.subscription.visit_limit
    visit_limit = forms.CharField(label='Добавить посещений')


class ClientSubscriptionForm(TenantModelForm):
    def __init__(self, *args, **kwargs):
        super(ClientSubscriptionForm, self).__init__(*args, **kwargs)
        choices = []
        choices.append(("", "--------------"))
        for st in SubscriptionsType.objects.all():
            choices.append((st.id, st.name))

        data = {'price': {'': ''}, 'visit_limit': {'': ''}}
        for f in SubscriptionsType.objects.all():
            data['price'][f.id] = f.price
            data['visit_limit'][f.id] = f.visit_limit

        self.fields['subscription'].widget = DataAttributesSelect(choices=choices, data=data)

    class Meta:
        model = ClientSubscriptions
        widgets = {
            'purchase_date': DatePickerInput(format='%d.%m.%Y',
                                             attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}),
            'start_date': DatePickerInput(format='%d.%m.%Y',
                                          attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}),
            'price': forms.TextInput(attrs={"class": "form-control", "placeholder": "Стоимость в рублях"}),
            'visits_left': forms.TextInput(attrs={"class": "form-control", "placeholder": "Кол-во посещений"}),
        }
        exclude = ('client', 'end_date')


class AttendanceForm(TenantModelForm):
    class Meta:
        model = Attendance
        exclude = ('client',)


class EventAttendanceForm(TenantModelForm):
    class Meta:
        model = Attendance
        exclude = ('event',)


class EventClassForm(TenantModelForm):
    class Meta:
        model = EventClass
        fields = ['name', 'location', 'coach', 'date_from', 'date_to',]
        widgets = {
            'date_from': DatePickerInput(format='%d.%m.%Y', attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}),
            'date_to': DatePickerInput(format='%d.%m.%Y', attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"}),
        }
        exclude = ('client',)


class DayOfTheWeekClassForm(TenantModelForm):

    checked = forms.BooleanField()

    class Meta:
        model = DayOfTheWeekClass
        fields = ('checked', 'start_time', 'end_time')
        widgets = {
            'start_time': TimePickerInput(),
            'end_time': TimePickerInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            # выставляем лейбл для чекбокса в зависимости от дня
            self.fields['checked'].label = _(calendar.day_name[kwargs['instance'].day])
        # Все поля делаем необязательными
        for key, field in self.fields.items():
            field.required = False
    # TODO: необходимо сделать проверку что если checked=true то остальные поля должны быть заполнены


class UserForm(TenantModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # Abstract user model dont't require names
        # Bur coach creation does
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class CoachForm(TenantModelForm):
    class Meta:
        model = Coach
        fields = '__all__'


class CoachMultiForm(MultiModelForm):
    form_classes = {
        'user': UserForm,
        # TODO: Add coach form after profile extending
        # 'coach': CoachForm
    }
