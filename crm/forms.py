import calendar

from betterforms.multiform import MultiModelForm
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput
from django import forms
from django.contrib.auth import get_user_model
from django.conf.locale.ru.formats import DATE_INPUT_FORMATS
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _
from django_select2.forms import (
    Select2Mixin, Select2MultipleWidget, Select2Widget,
)
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from contrib.forms import NonTenantUsernameMixin, TenantForm, TenantModelForm
from crm.utils import VK_PAGE_REGEXP
from .models import (
    Client, ClientBalanceChangeHistory, ClientSubscriptions, Coach,
    DayOfTheWeekClass, EventClass, Location, Manager, SubscriptionsType,
    Company,
)


class Select2ThemeMixin:
    def build_attrs(self, *args, **kwargs):
        self.attrs.setdefault('data-theme', 'bootstrap')
        return super().build_attrs(*args, **kwargs)


class Select2SingleTagMixin:
    def build_attrs(self, *args, **kwargs):
        self.attrs.setdefault('data-tags', 'true')
        return super().build_attrs(*args, **kwargs)


class Select2SingleTagWidget(
    Select2SingleTagMixin,
    Select2ThemeMixin,
    Select2Mixin,
    forms.Select
):
    pass


class ClientForm(TenantModelForm):
    birthday = forms.DateField(
        label='Дата рождения',
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=DatePickerInput(
            format='%d.%m.%Y',
            attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"},
            options={
                'locale': 'ru'
            }
        )
    )

    class Meta:
        model = Client

        fields = [
            'name', 'address', 'birthday', 'phone_number',
            'email_address', 'vk_user_id', 'additional_info',
        ]
        widgets = {
            'address': forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Адрес проживания"
                }
            ),
            'name': forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ФИО"}
            ),
            'phone_number': PhoneNumberInternationalFallbackWidget(
                attrs={'data-phone': True}
            ),
            'email_address': forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "example@email.com"}
            ),
            'additional_info': forms.Textarea(
                attrs={
                    "class": "form-control",
                }
            ),
            'vk_user_id': forms.HiddenInput(),
        }


class Balance(TenantModelForm):
    class Meta:
        model = ClientBalanceChangeHistory
        widgets = {
            'change_value': forms.NumberInput(),
            'reason': Select2SingleTagWidget(
                choices=[
                    ('Пополнение баланса', 'Пополнение баланса'),
                    ('Покупка абонемента', 'Покупка абонемента'),
                    ('Разовое посещение', 'Разовое посещение'),
                    ('Исправление ошибки', 'Исправление ошибки'),
                    ('Иное', 'Иное'),
                ],
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Укажите причину изменения баланса'
                }
            ),
            'client': forms.HiddenInput()
        }
        labels = {
            'change_value': 'Сумма пополнения, ₽'
        }
        exclude = ('entry_date', 'subscription')


class DataAttributesSelect(forms.Select):

    def __init__(self, attrs=None, choices=(), data=None):
        super().__init__(attrs, choices)
        self.data = data or {}

    def create_option(self, name, value, label, selected, index, subindex=None,
                      attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=None, attrs=None)
        for data_attr, values in self.data.items():
            option['attrs'][data_attr] = values[option['value']]

        return option


class SubscriptionsTypeForm(TenantModelForm):
    class Meta:
        model = SubscriptionsType
        fields = '__all__'


class SignUpClientWithoutSubscriptionForm(TenantForm):
    client = forms.ModelMultipleChoiceField(
        queryset=Client.objects.all(),
        label='Ученик',
        widget=Select2MultipleWidget
    )


class ExtendClientSubscriptionForm(TenantForm):
    visit_limit = forms.IntegerField(label='Добавить посещений', initial=1)
    reason = forms.CharField(label='Причина продления', widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.subscription = kwargs.pop('subscription')
        super(ExtendClientSubscriptionForm, self).__init__(*args, **kwargs)


class Select2ThemedMixin:
    """
    Mixin that enables bootstrap theme for Select2Widgets

    It can be used only for Select2Widgets, as assumes that function _get_media
    is defined in parent class
    """

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.setdefault('data-theme', 'bootstrap')
        return attrs

    def _get_media(self):
        media = (
            super()._get_media() + forms.Media(
            css={
                'screen': (
                    'https://cdnjs.cloudflare.com/ajax/libs/select2-bootstrap-theme/0.1.0-beta.10/select2-bootstrap.min.css',
                # noqa
                )
            })
        )
        return media

    media = property(_get_media)


class Select2WidgetAttributed(Select2ThemedMixin, Select2Widget):
    option_inherits_attrs = True

    def __init__(self, attrs=None, choices=(), attr_getter=lambda x: None):
        self.attr_geter = attr_getter
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None,
                      attrs=None):
        attrs = self.attr_geter(value) if value else None
        return super().create_option(
            name, value, label, selected, index, subindex=None,
            attrs=attrs)


def subcription_type_attrs(sub_id):
    try:
        subs = SubscriptionsType.objects.get(id=sub_id)
    except SubscriptionsType.DoesNotExist:
        return None
    return {
        'data-price': subs.price,
        'data-visits': subs.visit_limit,
        'data-onetime': int(subs.one_time),
    }


class InplaceSellSubscriptionForm(TenantModelForm):
    cash_earned = forms.BooleanField(
        label='Деньги получены',
        required=False,
        initial=True
    )
    subscription = forms.ModelChoiceField(
        empty_label='',
        queryset=SubscriptionsType.objects.exclude(one_time=True),
        label='Абонемент',
        widget=Select2WidgetAttributed(
            attr_getter=subcription_type_attrs)
    )
    start_date = forms.DateField(
        label='Начало действия',
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = ClientSubscriptions

        widgets = {
            'price': forms.TextInput(
                attrs={"placeholder": "Стоимость в рублях"}
            ),
            'client': forms.HiddenInput(),

        }
        exclude = ('purchase_date', 'end_date', 'visits_on_by_time')

    def __init__(self, *args, **kwargs):
        st_qs = kwargs.pop(
            'subscription_type_qs',
            SubscriptionsType.objects.exclude(one_time=True)
        )
        super().__init__(*args, **kwargs)

        self.fields['subscription'].queryset = st_qs


class ClientSubscriptionForm(TenantModelForm):
    cash_earned = forms.BooleanField(
        label='Деньги получены',
        required=False,
        initial=True
    )
    subscription = forms.ModelChoiceField(
        empty_label='',
        queryset=SubscriptionsType.objects.all(),
        label='Абонемент',
        widget=Select2WidgetAttributed(
            attr_getter=subcription_type_attrs)
    )
    start_date = forms.DateField(
        label='Дата начала',
        initial=timezone.localdate(),
        input_formats=DATE_INPUT_FORMATS,
        widget=DatePickerInput(
            format='%d.%m.%Y',
            attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"},
            options={
                'locale': 'ru'
            }
        )
    )

    class Meta:
        model = ClientSubscriptions

        widgets = {
            'client': forms.HiddenInput(),
            'price': forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Стоимость в рублях"
                }
            ),
            'visits_left': forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Кол-во посещений"
                }
            ),
        }
        labels = {
            'start_date': 'Начало действия',
            'visits_left': 'Количество посещений'
        }
        exclude = ('purchase_date', 'end_date', 'visits_on_by_time')

    def __init__(self, *args, **kwargs):
        disable_subscription_type = kwargs.pop(
            'disable_subscription_type', False)
        activated_subscription = kwargs.pop(
            'activated_subscription', False)

        super(ClientSubscriptionForm, self).__init__(*args, **kwargs)

        # Set subscription queryset on init, as if it will be defined in
        # class field initialization, it will ignore SafeDeleteMixin
        if not disable_subscription_type:
            self.fields['subscription'].queryset = \
                SubscriptionsType.objects.exclude(one_time=True)
        else:
            self.fields['subscription'].disabled = True
            # Select all subscriptions, as field is non-editable, and
            # we can safely display subscription type, event it was in
            # archive
            self.fields['subscription'].queryset = \
                SubscriptionsType.all_objects.exclude(one_time=True)

        if activated_subscription:
            for __, field in self.fields.items():
                field.disabled = True


class EventClassForm(TenantModelForm):
    one_time_price = forms.IntegerField(
        label='Стоимость разового посещения',
        initial='',
        min_value=0,
        required=False
    )
    location = forms.ModelChoiceField(
        empty_label='',
        queryset=Location.objects.all(),
        label='Место проведения',
        widget=Select2WidgetAttributed(
            attr_getter=subcription_type_attrs)
    )
    coach = forms.ModelChoiceField(
        empty_label='',
        queryset=Coach.objects.all(),
        label='Тренер',
        widget=Select2WidgetAttributed(
            attr_getter=subcription_type_attrs)
    )
    date_from = forms.DateField(
        label='Начало тренировок',
        input_formats=DATE_INPUT_FORMATS,
        widget=DatePickerInput(
            format='%d.%m.%Y',
            attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"},
            options={
                'locale': 'ru'
            }
        ),
        required=False
    )
    date_to = forms.DateField(
        label='Окончание тренировок',
        input_formats=DATE_INPUT_FORMATS,
        widget=DatePickerInput(
            format='%d.%m.%Y',
            attrs={"class": "form-control", "placeholder": "ДД.MM.ГГГГ"},
            options={
                'locale': 'ru'
            }
        ),
        required=False
    )

    class Meta:
        model = EventClass
        fields = [
            'name', 'location', 'coach', 'date_from', 'date_to',
            'one_time_price'
        ]
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
            self.fields['checked'].label = \
                _(calendar.day_name[kwargs['instance'].day])
        # Все поля делаем необязательными
        for key, field in self.fields.items():
            field.required = False
        # TODO: необходимо сделать проверку что если checked=true то остальные
        #  поля должны быть заполнены


@deconstructible
class FakeNameValidator:
    message = (
        'Не хватает данных для ФИО. '
        'Возможно вы забыли указать фамилию или имя'
    )
    code = 'not_fullname'

    def __call__(self, value):
        if len(value.strip().split(maxsplit=1)) < 2:
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.message == other.message and
            self.code == other.code
        )


class ProfileUserForm(NonTenantUsernameMixin, TenantModelForm):
    fullname = forms.CharField(
        label='ФИО',
        widget=forms.TextInput(attrs={'data-name-edit': True})
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.HiddenInput(),
            'last_name': forms.HiddenInput()
        }
        labels = {
            'username': 'Логин'
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        instance = kwargs.get('instance', None)

        if instance:
            if initial is None:
                initial = {}
            initial['fullname'] = instance.get_full_name()

        super(ProfileUserForm, self).__init__(*args, initial=initial, **kwargs)


class UserForm(TenantModelForm):
    fullname = forms.CharField(
        label='ФИО',
        required=True,
        widget=forms.TextInput(attrs={'data-name-edit': True})
    )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name')
        widgets = {
            'first_name': forms.HiddenInput(),
            'last_name': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        instance = kwargs.get('instance', None)

        if instance:
            if initial is None:
                initial = {}
            initial['fullname'] = instance.get_full_name()

        super(UserForm, self).__init__(*args, initial=initial, **kwargs)


class CoachForm(TenantModelForm):
    vk_page = forms.RegexField(
        label='Страница VK',
        regex=VK_PAGE_REGEXP,
        required=False
    )

    class Meta:
        model = Coach
        fields = ('phone_number',)
        widgets = {
            'phone_number': PhoneNumberInternationalFallbackWidget(
                attrs={'data-phone': True}
            )
        }


class ManagerForm(TenantModelForm):
    vk_page = forms.RegexField(
        label='Страница VK',
        regex=VK_PAGE_REGEXP,
        required=False
    )

    class Meta:
        model = Manager
        fields = ('phone_number',)
        widgets = {
            'phone_number': PhoneNumberInternationalFallbackWidget(
                attrs={'data-phone': True}
            )
        }


class CoachMultiForm(MultiModelForm):
    form_classes = {
        'user': UserForm,
        'coach': CoachForm
    }


class ManagerMultiForm(MultiModelForm):
    form_classes = {
        'user': UserForm,
        'manager': ManagerForm
    }


class ProfileManagerForm(MultiModelForm):
    form_classes = {
        'user': ProfileUserForm,
        'detail': ManagerForm
    }


class ProfileCoachForm(MultiModelForm):
    form_classes = {
        'user': ProfileUserForm,
        'detail': CoachForm
    }


class UploadExcelForm(forms.Form):
    file = forms.FileField(label='Файл Excel',  help_text="Файл в формате excel")
    ignore_first_row = forms.BooleanField(label='Не учитывать первую строку', initial=False, required=False)
    name_col = forms.CharField(label='Столбец с ФИО', initial='A', help_text="Буква столбца с ФИО")
    phone_col = forms.CharField(label='Столбец с номером телефона', initial='B', help_text="Буква столбца с номером телефона. Номер телефона в русском формате")
    birthday_col = forms.CharField(label='Столбец с датой рождения', initial='C', help_text="Буква столбца с датой рождения. Допустимые форматы даты: ГГГГ-ММ-ДД, ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ")
    vk_col = forms.CharField(label='Столбец со ссылкой вк', initial='D', help_text="Буква столбца со ссылкой на vk. Формат ссылки: vk.com/user_id или https://vk.com/user_id")
    balance_col = forms.CharField(label='Столбец с балансом', initial='E', help_text="Буква столбца с балансом")


class CompanyForm(forms.ModelForm):
    active_to_display = forms.CharField(
        label='Компания активна до',
        required=False,
        disabled=True,
        widget=forms.TextInput()
    )

    class Meta:
        model = Company
        exclude = ('name', 'active_to')
        labels = {
            'display_name': 'Название',
            'vk_group_id': 'Идентификатор сообщества в Вконтакте',
            'vk_access_token': 'Токен доступа к сообщениям',
            'vk_confirmation_token': 'Код подтверждения бота'
        }
        help_texts = {
            'vk_group_id': 'Нужен если вы используете эту возможноть.',
            'vk_access_token': 'Токен доступа с правами отправки сообщений.'
                               'Необходим для того чтобы бот мог отправлять '
                               'сообщения от имени сообщества',
            'vk_confirmation_token': 'Необходим для первичной привязки бота к '
                                     'сообществу. Нужен только один раз.',
            'active_to': 'Дата, до котрой актвина подписка компании'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        self.fields['active_to_display'].initial = (
            f'{instance.active_to:%d.%m.%Y}' if instance and instance.active_to
            else 'без ограничений'
        )
