
from django import forms
from bootstrap_datepicker_plus import DatePickerInput
from django.db.models import QuerySet
from django.forms import ModelChoiceField
from django.utils.html import conditional_escape, escape
from jwt.utils import force_unicode

from .models import Client, ClientSubscriptions, Attendance, SubscriptionsType


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client

        fields = ['name', 'address',
                  'birthday', 'phone_number', 'email_address', 'vk_user_id']
        widgets = {
            'birthday': DatePickerInput(format='%Y-%m-%d', attrs={"class": "form-control", "placeholder":"ГГГГ-ММ-ДД"}),
            'address': forms.TextInput(attrs={"class": "form-control", "placeholder":"Адрес проживания"}),
            'name': forms.TextInput(attrs={"class": "form-control", "placeholder":"ФИО"}),
            'phone_number': forms.TextInput(attrs={"class": "form-control", "placeholder":"Номер телефона"}),
            'email_address': forms.EmailInput(attrs={"class": "form-control", "placeholder":"example@mail.com"}),
        }

class ChoiceFieldWithTitles(forms.ChoiceField):
    widget = forms.Select

    def __init__(self, choices=(), *args, **kwargs):
        choice_pairs = [(c[0], c[1]) for c in choices]
        super(ChoiceFieldWithTitles, self).__init__(choices=choice_pairs, *args, **kwargs)

class ClientSubscriptionForm(forms.ModelForm):

    subscription = ChoiceFieldWithTitles()

    def __init__(self, *args, **kwargs):
        super(ClientSubscriptionForm, self).__init__(*args, **kwargs)
        choices = []
        for st in SubscriptionsType.objects.all():
            choices.append(( st.price, st.name))
        self.fields['subscription'] = ChoiceFieldWithTitles(choices=choices)

    class Meta:
        model = ClientSubscriptions
        widgets = {
            'purchase_date': DatePickerInput(format='%Y-%m-%d',
                                        attrs={"class": "form-control", "placeholder": "ГГГГ-ММ-ДД"}),
            'start_date': DatePickerInput(format='%Y-%m-%d',
                                             attrs={"class": "form-control", "placeholder": "ГГГГ-ММ-ДД"}),
            'price': forms.TextInput(attrs={"class": "form-control", "placeholder": ""}),
            'visits_left': forms.TextInput(attrs={"class": "form-control", "placeholder": "Оставшееся кол-во занятий"}),
        }
        exclude = ('client',)


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        exclude = ('client',)
