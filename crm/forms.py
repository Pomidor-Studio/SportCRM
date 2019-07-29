from betterforms.multiform import MultiModelForm
from django import forms
from django.conf.locale.ru.formats import DATE_INPUT_FORMATS
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxSelectMultiple, TextInput
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django_select2.forms import (
    Select2Mixin, Select2Widget,
)
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from contrib.forms import NonTenantUsernameMixin, TenantForm, TenantModelForm
from contrib.vk_utils import get_vk_id_from_page_link
from crm.utils import VK_PAGE_REGEXP
from .models import (
    Client, ClientBalanceChangeHistory, ClientSubscriptions, Coach, Company,
    Event, Manager, SubscriptionsType,
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
    vk_page = forms.RegexField(
        label='Профиль в Вконтакте',
        regex=VK_PAGE_REGEXP,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "vk.com/id234533221"},
        )
    )

    birthday = forms.DateField(
        label='Дата рождения',
        required=False,
        input_formats=DATE_INPUT_FORMATS,
    )

    class Meta:
        model = Client

        fields = [
            'name', 'address', 'birthday', 'phone_number',
            'email_address', 'additional_info',
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
                attrs={'data-phone': True, "placeholder": "+7 919 123 45 67"}
            ),
            'email_address': forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "example@email.com"}
            ),
            'additional_info': forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": "4",
                    "placeholder": "Здесь вы можете указать информацию о клиенте и дополнительные номера телефонов",
                }
            )
        }

    def save(self, commit=True):
        instance = super().save(commit)
        vk_page = self.cleaned_data['vk_page']
        instance.vk_user_id = get_vk_id_from_page_link(vk_page)
        instance.save()
        return instance


class Balance(TenantModelForm):
    go_back = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = ClientBalanceChangeHistory
        widgets = {
            'change_value': forms.NumberInput(),
            'reason': forms.TextInput(
                attrs={
                    'placeholder': 'Комментарий'
                }
            ),
            'client': forms.HiddenInput(),
            'changed_by': forms.HiddenInput(),
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
    duration = forms.IntegerField(label='Продолжительность', min_value=1)
    visit_limit = forms.IntegerField(label='Количество посещений', min_value=1)

    class Meta:
        model = SubscriptionsType
        fields = '__all__'
        widgets = {
            'event_class': CheckboxSelectMultiple(),
        }


class SignUpClientWithoutSubscriptionForm(TenantForm):
    client = forms.ModelMultipleChoiceField(
        queryset=Client.objects,
        label='Ученик',
        widget=forms.SelectMultiple(
            attrs={
                'class': 'selectpicker form-control',
                'multiple': '',
                'data-selected-text-format': 'static',
                'title': 'Выбрать ученика',
                'placeholder': 'Выбрать ученика'
            }
        ),
    )


class SignUpClientMultiForm(MultiModelForm):
    form_classes = {
        'exists': SignUpClientWithoutSubscriptionForm,
        'new': ClientForm
    }

    def is_valid(self):
        return any(form.is_valid() for form in self.forms.values())


class ExtendClientSubscriptionForm(TenantForm):
    visit_limit = forms.IntegerField(
        label='Добавить посещений',
        initial=1,
        min_value=1
    )
    reason = forms.CharField(label='Причина продления', widget=forms.TextInput)
    go_back = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        self.subscription = kwargs.pop('subscription')
        super(ExtendClientSubscriptionForm, self).__init__(*args, **kwargs)

    def clean_visit_limit(self):
        max_add = self.subscription.max_visits_to_add
        if max_add <= 0:
            raise ValidationError(
                'Этот абонемент нельзя продлить, так как клиент может '
                'посетить все оставшиеся у него занятия, до даты окончания '
                'абонемента.', code='invalid-visits-limit')

        if self.cleaned_data['visit_limit'] > max_add:
            raise ValidationError(
                'Нельзя указывать больше визитов, чем клиент пропустил '
                '({})'.format(max_add),
                code='invalid-visits-limit'
            )
        return self.cleaned_data['visit_limit']


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
        exclude = ('purchase_date', 'end_date', 'visits_on_by_time',
                   'event_class', 'sold_by')

    def __init__(self, *args, **kwargs):
        st_qs = kwargs.pop(
            'subscription_type_qs',
            SubscriptionsType.objects.exclude(one_time=True)
        )
        super().__init__(*args, **kwargs)

        self.fields['subscription'].queryset = st_qs


class ClientSubscriptionForm(TenantModelForm):
    error_css_class = 'is-invalid'

    cash_earned = forms.BooleanField(
        label='Деньги получены',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': "form-check-input"}
        )
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
        widget=forms.DateInput(
            format='%d.%m.%Y',
            attrs={
                "class": "form-control",
                "placeholder": "ДД.MM.ГГГГ",
                "dp_config": '{&quot;id&quot;: &quot;dp_7&quot;, &quot;picker_type&quot;: &quot;DATE&quot;, &quot;linked_to&quot;: null, &quot;options&quot;: {&quot;showClose&quot;: true, &quot;showClear&quot;: true, &quot;showTodayButton&quot;: true, &quot;locale&quot;: &quot;ru&quot;, &quot;format&quot;: &quot;DD.MM.YYYY&quot;}}',
            },
        )
    )
    go_back = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = ClientSubscriptions

        widgets = {
            'client': forms.HiddenInput(),
            'sold_by': forms.HiddenInput(),
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
            'visits_left': 'Лимит занятий'
        }
        exclude = ('purchase_date', 'end_date', 'visits_on_by_time',
                   'event_class',)

    def __init__(self, *args, **kwargs):
        disable_subscription_type = kwargs.pop(
            'disable_subscription_type', False)
        activated_subscription = kwargs.pop(
            'activated_subscription', False)
        for_event_class = kwargs.pop('event_class', None)  # type: Event

        super(ClientSubscriptionForm, self).__init__(*args, **kwargs)

        # Set subscription queryset on init, as if it will be defined in
        # class field initialization, it will ignore SafeDeleteMixin
        if not disable_subscription_type:
            qs = SubscriptionsType.objects.all()
        else:
            self.fields['subscription'].disabled = True
            # Select all subscriptions, as field is non-editable, and
            # we can safely display subscription type, event it was in
            # archive
            qs = SubscriptionsType.all_objects.all()

        if for_event_class:
            qs = qs.filter(event_class=for_event_class)
        else:
            qs = qs.exclude(one_time=True)

        self.fields['subscription'].queryset = qs

        if activated_subscription:
            for __, field in self.fields.items():
                field.disabled = True


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
        fields = ('first_name', 'last_name', 'email')
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
        label='Профиль в Вконтакте',
        regex=VK_PAGE_REGEXP,
        required=False
    )

    class Meta:
        model = Coach
        fields = ('phone_number',)
        widgets = {
            'phone_number': PhoneNumberInternationalFallbackWidget(
                attrs={'data-phone': True}
            ),
            'vk_page': TextInput(
                attrs={'placeholder': 'Ссылка на страницу пользователя'}
            )
        }


class ManagerForm(TenantModelForm):
    vk_page = forms.RegexField(
        label='Профиль в Вконтакте',
        regex=VK_PAGE_REGEXP,
        required=False,
        widget=TextInput(
            attrs={'placeholder': 'Ссылка на страницу пользователя', 'class': 'form-control'}
        )
    )

    class Meta:
        model = Manager
        fields = ('phone_number',)
        widgets = {
            'phone_number': PhoneNumberInternationalFallbackWidget(
                attrs={'data-phone': True}
            ),
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
    file = forms.FileField(label='Файл Excel', help_text="Файл в формате Excel. Первая строка в таблице не учитывается.")
    #ignore_first_row = forms.BooleanField(label='Не учитывать первую строку', initial=False, required=False)
    name_col = forms.CharField(label='Столбец с ФИО', initial='A', help_text="Буква столбца с ФИО")
    phone_col = forms.CharField(label='Столбец с номером телефона', initial='B',
                                help_text="Буква столбца с номером телефона. Номер телефона в русском формате")
    birthday_col = forms.CharField(label='Столбец с датой рождения', initial='C',
                                   help_text="Буква столбца с датой рождения. Допустимые форматы даты: ГГГГ-ММ-ДД, ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ")
    vk_col = forms.CharField(label='Столбец со ссылкой вк', initial='D',
                             help_text="Буква столбца со ссылкой на vk. Формат ссылки: vk.com/user_id или https://vk.com/user_id")
    balance_col = forms.CharField(label='Столбец с балансом', initial='E', help_text="Буква столбца с балансом")


class CompanyForm(forms.ModelForm):
    active_to_display = forms.CharField(
        label='Компания активна до',
        required=False,
        disabled=True,
        widget=forms.TextInput()
    )
    display_name = forms.CharField(
        label='Название',
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
