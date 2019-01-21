from django import forms
from bootstrap_datepicker_plus import DatePickerInput
from .models import Client, ClientSubscriptions, Attendance


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


class ClientSubscriptionForm(forms.ModelForm):
    class Meta:
        model = ClientSubscriptions
        widgets = {
            'purchase_date': DatePickerInput(format='%Y-%m-%d',
                                        attrs={"class": "form-control", "placeholder": "ГГГГ-ММ-ДД"}),
            'start_date': DatePickerInput(format='%Y-%m-%d',
                                             attrs={"class": "form-control", "placeholder": "ГГГГ-ММ-ДД"}),
            'price': forms.TextInput(attrs={"class": "form-control", "placeholder": "Цена в рублях"}),
            'visits_left': forms.TextInput(attrs={"class": "form-control", "placeholder": "Оставшееся кол-во занятий"}),
        }
        exclude = ('client',)


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        exclude = ('client',)
