from django import forms
from bootstrap_datepicker_plus import DatePickerInput
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client

        fields = ['name', 'address',
                  'birthday', 'phone_number', 'email_address', 'vk_user_id']
        widgets = {
            'birthday': DatePickerInput(format='%Y-%m-%d', attrs={"class": "form-control", "placeholder":"ГГГГ-ММ-ДД"}),
            'address': forms.TextInput(attrs={"class": "form-control ml-4 mb-2", "placeholder":"Адрес проживания"}),
            'name': forms.TextInput(attrs={"class": "form-control ml-4 mb-2", "placeholder":"ФИО"}),
            'phone_number': forms.TextInput(attrs={"class": "form-control ml-4 mb-2", "placeholder":"Номер телефона"}),
            'email_address': forms.EmailInput(attrs={"class": "form-control ml-4 mb-2", "placeholder":"example@mail.com"}),
        }
