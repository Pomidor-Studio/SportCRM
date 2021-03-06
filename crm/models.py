from __future__ import annotations

import logging
import decimal
import uuid
from datetime import date, datetime, timedelta, time
from itertools import count
from typing import Callable, Dict, List, Optional

import pendulum
import reversion
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction, utils
from django.db.models import Q, Model, Count, F, Sum
from django.db.models.manager import BaseManager
from django.forms import forms
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django_multitenant.fields import TenantForeignKey
from django_multitenant.mixins import TenantManagerMixin, TenantQuerySet
from django_multitenant.models import TenantModel
from django_multitenant.utils import get_current_tenant, set_current_tenant
from phonenumber_field.modelfields import PhoneNumberField
from psycopg2 import Error as Psycopg2Error
from safedelete.managers import (
    SafeDeleteAllManager, SafeDeleteDeletedManager, SafeDeleteManager,
)
from safedelete.models import SafeDeleteModel
from transliterate import translit

from crm.enums import GRANULARITY
from crm.events import get_nearest_to, next_day, Weekdays, extend_range_distance
from contrib.text_utils import pluralize

INTERNAL_COMPANY = 'INTERNAL'

logger = logging.getLogger('crm.models')


class NoFutureEvent(Exception):
    pass


class ScrmTenantManagerMixin:
    """
    Override TenantManagerMixin behaviour, as it ignore that queryset may be
    already instance of TenantQuerySet
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        if not isinstance(queryset, TenantQuerySet):
            queryset = TenantQuerySet(self.model)

        current_tenant = get_current_tenant()
        if current_tenant:
            current_tenant_id = getattr(current_tenant, current_tenant.tenant_id, None)

            # TO CHANGE: tenant_id should be set in model Meta
            kwargs = {self.model.tenant_id: current_tenant_id}

            return super().get_queryset().filter(**kwargs)
        return queryset


class ScrmSafeDeleteManager(ScrmTenantManagerMixin, SafeDeleteManager):
    pass


class ScrmSafeDeleteAllManager(ScrmTenantManagerMixin, SafeDeleteAllManager):
    pass


class ScrmSafeDeleteDeletedManager(
    ScrmTenantManagerMixin,
    SafeDeleteDeletedManager
):
    pass


class ScrmSafeDeleteModel(SafeDeleteModel):
    objects = ScrmSafeDeleteManager()
    all_objects = ScrmSafeDeleteAllManager()

    deleted_objects = ScrmSafeDeleteDeletedManager()

    class Meta:
        abstract = True


@reversion.register()
class Company(models.Model):
    """Компания. Multitentant строится вокруг этой модели"""

    # Внутренее поле, нужное для работы административных аккаунтов
    # По факту является своеобразным uuid
    name = models.CharField("Название", max_length=100, unique=True)
    display_name = models.CharField('Отображаемое название', max_length=100)
    vk_group_id = models.CharField(
        'ИД группы вк',
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    vk_access_token = models.CharField(
        'Токен группы вк',
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    vk_confirmation_token = models.CharField(
        'Строка-подтверждение',
        max_length=20,
        null=True,
        blank=True
    )
    # Active to - means that company can access to site, and data until
    # date. If `active_to` is None, it means that company have unlimited
    # access, without any restriction
    active_to = models.DateField('Компания активна до', null=True, blank=True)
    tenant_id = 'id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orig_display_name = self.display_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Generate translit name only if display name is changed by someone
        if self._orig_display_name != self.display_name:
            for idx in count(start=1):
                trans_name = translit(
                    self.display_name, language_code='ru', reversed=True)
                name = trans_name.replace(' ', '_').lower()
                inner_name = f'{idx}_{name}'[:100]
                if not Company.objects.filter(name=inner_name).exists():
                    self.name = inner_name
                    break

        # Disallow ability to change activity date for internal company
        if self.display_name == INTERNAL_COMPANY and self.active_to is not None:
            raise forms.ValidationError(
                'Нельзя менять дату активности у компании INTERNAL!')

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.display_name


class CustomUserManager(TenantManagerMixin, UserManager):
    def generate_uniq_username(self, first_name, last_name, prefix='user'):
        # Disable current tenant for avoiding username collation between
        # companies
        current_tenant = get_current_tenant()
        set_current_tenant(None)
        name = 'nevenr_used_name'
        for idx in count():
            trans_f = translit(first_name, language_code='ru', reversed=True)
            trans_l = translit(last_name, language_code='ru', reversed=True)
            name = f'{prefix}_{idx}_{trans_f}_{trans_l}'.lower()[:150]

            if not self.filter(username=name).exists():
                break

        set_current_tenant(current_tenant)
        return name

    def create_coach(self, first_name, last_name):
        return self.create_user(
            self.generate_uniq_username(first_name, last_name, prefix='coach'),
            first_name=first_name, last_name=last_name,
            company=get_current_tenant()
        )


def get_user_current_tenant():
    """
    Hack, to provide way for admin user creations
    """
    current_tenant = get_current_tenant()
    if current_tenant is None:
        try:
            return (
                Company.objects
                    .only('id')
                    .filter(name=INTERNAL_COMPANY)
                    .first()
            )
        except (Company.DoesNotExist, Psycopg2Error, utils.Error):
            return None


@reversion.register()
class User(TenantModel, AbstractUser):
    company = models.ForeignKey(
        Company,
        default=get_user_current_tenant,
        on_delete=models.PROTECT
    )
    tenant_id = 'company_id'

    objects = CustomUserManager()

    @property
    def is_coach(self) -> bool:
        return hasattr(self, 'coach')

    @property
    def is_manager(self) -> bool:
        return hasattr(self, 'manager')

    @property
    def has_vk_auth(self) -> bool:
        return self.social_auth.filter(provider='vk-oauth2').exists()

    @property
    def vk_id(self) -> Optional[str]:
        return self.vk_data('id') or self.vk_data('uid')

    @property
    def vk_link(self) -> Optional[str]:
        vkid = self.vk_id
        return 'https://vk.com/id{}'.format(vkid) if vkid else None

    def vk_data(self, data_key: str) -> Optional[str]:
        try:
            social = self.social_auth.get(provider='vk-oauth2')
        except models.ObjectDoesNotExist:
            return None

        if data_key == 'uid':
            return social.uid

        return social.extra_data.get(data_key)

    @property
    def vk_message_token(self) -> str:
        return self.company.vk_access_token

    def __str__(self):
        return self.get_full_name() or 'Имя не указано'


class CompanyObjectModel(TenantModel):
    """Абстрактный класс для разделяемых по компаниям моделей"""
    company = models.ForeignKey(
        Company,
        default=get_current_tenant,
        on_delete=models.PROTECT
    )
    tenant_id = 'company_id'

    class Meta:
        abstract = True
        unique_together = ["id", "company"]


@reversion.register()
class Location(ScrmSafeDeleteModel, CompanyObjectModel):
    name = models.CharField("Название", max_length=100)
    address = models.CharField("Адрес", max_length=1000, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('crm:manager:locations:list')

    @property
    def has_active_events(self):
        today = timezone.now().date()
        return self.eventclass_set.filter(
            Q(date_to__gt=today)
        ).exists()


@reversion.register()
class Coach(ScrmSafeDeleteModel, CompanyObjectModel):
    """
    Профиль тренера
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    phone_number = PhoneNumberField("Телефон", blank=True)

    def __str__(self):
        return self.user.get_full_name() or 'Имя не указано'

    def get_absolute_url(self):
        return reverse('crm:manager:coach:update', kwargs={'pk': self.pk})

    @property
    def has_active_events(self):
        today = timezone.now().date()
        return self.eventclass_set.filter(
            Q(date_from__gt=today) |
            Q(date_to__gt=today)
        ).exists()


@reversion.register()
class Manager(ScrmSafeDeleteModel, CompanyObjectModel):
    """
    Профиль менеджера
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    phone_number = PhoneNumberField("Телефон", blank=True)

    def __str__(self):
        return self.user.get_full_name() or 'Имя не указано'

    def get_absolute_url(self):
        return reverse('crm:manager:manager:update', kwargs={'pk': self.pk})


class EventClassManager(TenantManagerMixin, models.Manager):
    def active(self):
        return self.get_queryset().filter(
            Q(date_to__isnull=True) | Q(date_to__gte=date.today())
        )

    def in_range(self, day_start, day_end):
        return self.get_queryset().filter(
            (
                Q(date_from__isnull=False) & Q(date_to__isnull=False) &
                Q(date_from__lte=day_end) & Q(date_to__gte=day_start)
            ) | (
                Q(date_from__isnull=False) & Q(date_to__isnull=True) &
                Q(date_from__lte=day_end)
            ) | (
                Q(date_from__isnull=True) & Q(date_to__isnull=False) &
                Q(date_to__gte=day_start)
            ) | (
                Q(date_from__isnull=True) & Q(date_to__isnull=True)
            )
        )


@reversion.register()
class EventClass(CompanyObjectModel):
    """
    Описание шаблона мероприятия (Класс вид).
    Например, тренировки в зале бокса у Иванова по средам и пятницам
    """
    name = models.CharField("Наименование", max_length=100)
    location = TenantForeignKey(
        Location,
        on_delete=models.PROTECT,
        verbose_name="Место проведения")
    coach = TenantForeignKey(
        Coach,
        on_delete=models.PROTECT,
        verbose_name="Тренер")
    date_from = models.DateField("Начало тренировок", null=True, blank=True)
    date_to = models.DateField("Окончание тренировок", null=True, blank=True)

    objects = EventClassManager()

    def get_one_time_visit_costs(self):
        return self.subscriptionstype_set.filter(one_time=True).first()

    @property
    def otv_price(self) -> Optional[float]:
        """
        Get one time visit (otv) price.
        :return: price of visit or None if no otv assigned to event class
        """
        otv = self.get_one_time_visit_costs()
        return otv.price if otv else None

    def days(self) -> List[int]:
        """
        Get list of all weekdays of current event

        For example: [0, 2, 4] for monday, wednesday, friday
        """
        return list(
            self.dayoftheweekclass_set
                .all()
                .order_by('day')
                .values_list('day', flat=True)
        )

    def is_event_day(self, day: date) -> bool:
        """
        Возможна ли тренировка в указанный день

        :param day: День который надо проверить
        :return: Является ли указанный день - днем тренировки
        """

        # Проверяем, входит ли проверяемый день в диапазон проводимых тренировок
        if (self.date_from and self.date_from > day) or \
            (self.date_to and self.date_to < day):
            return False

        # Проверяем, проходят ли в этот день недели тренировки
        weekdays = self.dayoftheweekclass_set.all()
        if weekdays:
            for weekday in weekdays:
                if weekday.day == day.weekday():
                    break
            else:
                # https://ncoghlan-devs-python-notes.readthedocs.io/en/latest/python_concepts/break_else.html
                return False

        return True

    def get_nearest_event_to(self, required_day: date):
        return get_nearest_to(
            required_day, Weekdays(self.days()), self.date_to)

    def get_nearest_event_to_or_none(
        self,
        required_day: date
    ) -> Optional[date]:
        try:
            return self.get_nearest_event_to(required_day)
        except ValueError:
            return None

    def get_calendar(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[date, Event]:
        """
        Создает полный календарь одного типа тренировки. Создается список
        всех возможный дней трениовок, ограниченный диапазоном дат.

        Сами события треннировки не создаются фактически, а могут появится лишь
        когда на эту тренировку будут назначены ученики.

        :param start_date: Начальная дата календаря
        :param end_date: Конечная дата календаря
        :return: Словарь из даты и возможной тренировки
        """
        if start_date is None or end_date is None:
            raise ValueError(
                'Calendar can be calculated only for fixed date range')

        events = {
            event.date: event
            for event in
            self.event_set.filter(date__range=(start_date, end_date))
        }

        if self.date_from and start_date < self.date_from:
            start_date = self.date_from

        if self.date_to and self.date_to < end_date:
            end_date = self.date_to

        days_time = {
            x['day']: (x['start_time'], x['end_time'])
            for x in
            self.dayoftheweekclass_set
                .all()
                .values('day', 'start_time', 'end_time')
        }

        for event_date in next_day(start_date, end_date, Weekdays(self.days())):
            if event_date not in events:
                event = Event(
                    date=event_date,
                    event_class=self
                )
                events[event_date] = event
            else:
                event = events[event_date]

            # Pre-set data to event can reduce response time in ten times
            # For example non-optimized response of full calendar for one month
            # is running for 929ms, after optimization only 80ms
            event.event_class_name = self.name
            try:
                event.start_time = days_time[event_date.weekday()][0]
                event.end_time = days_time[event_date.weekday()][1]
            except KeyError:
                pass

        return events

    # TODO: Нужны методы:
    #   - Создание нового event
    #       +Получение на конкретную дату
    #   - Валидация всех event (а можно ли редактировать описание
    #   тренировки, если они уже были?)

    @staticmethod
    def get_absolute_url():
        return reverse_lazy('crm:manager:event-class:list')

    def __str__(self):
        return self.name

    @property
    def detailed_name(self):
        return f'{self.name} y {self.coach} в {self.location}'


@reversion.register()
class DayOfTheWeekClass(CompanyObjectModel):
    """
    Мероприятие в конкретный день недели, в определенное время,
    определенной продолжительности
    """
    event = TenantForeignKey(
        EventClass,
        on_delete=models.CASCADE,
        verbose_name="Мероприятие"
    )
    # номер дня недели
    day = models.PositiveSmallIntegerField(
        "День недели",
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    start_time = models.TimeField(
        "Время начала тренировки",
        default=time(19)
    )
    end_time = models.TimeField(
        "Время окнчания тренировки",
        default=time(20)
    )

    class Meta:
        unique_together = ('day', 'event',)

    def __str__(self):
        return f'{self.event} {self.day+1}'


# noinspection PyPep8Naming
class SubscriptionsTypeEventFilter:
    @staticmethod
    def ALL(event: Event) -> bool:
        return True

    @staticmethod
    def ACTIVE(event: Event) -> bool:
        return not event.is_canceled

    @staticmethod
    def CANCELED(event: Event) -> bool:
        return event.is_canceled


@reversion.register()
class SubscriptionsType(ScrmSafeDeleteModel, CompanyObjectModel):
    """
    Типы абонементов
    Описывает продолжительность действия, количество посещений,
    какие тренировки позволяет посещать
    """
    name = models.CharField("Наименование", max_length=100)
    price = models.FloatField("Цена, ₽")
    duration = models.PositiveIntegerField("Продолжительность")
    duration_type = models.CharField(
        "Временные рамки абонемента",
        max_length=20,
        choices=GRANULARITY,
        default=GRANULARITY.DAY
    )
    rounding = models.BooleanField(
        "Округление начала действия абонемента",
        default=False
    )
    visit_limit = models.PositiveIntegerField("Количество посещений")
    event_class = models.ManyToManyField(
        EventClass,
        verbose_name="Допустимые тренировки"
    )
    one_time = models.BooleanField(
        "Разовый абонемент",
        editable=False,
        default=False
    )

    def __str__(self):
        return self.name

    def start_date(self, rounding_date: date) -> pendulum.Date:
        """
        Возвращает дату начала действия абонемента после округления.

        :param rounding_date: дата начала действия абонемента до округления
        """
        p_date: pendulum.Date = pendulum.Date.fromordinal(
            rounding_date.toordinal())
        if not self.rounding:
            return p_date

        elif self.duration_type == GRANULARITY.DAY:
            return p_date

        elif self.duration_type == GRANULARITY.WEEK:
            return p_date.start_of('week')

        elif self.duration_type == GRANULARITY.MONTH:
            return p_date.start_of('month')

        elif self.duration_type == GRANULARITY.YEAR:
            return p_date.start_of('year')

        return p_date

    def end_date(self, start_date: date) -> Optional[pendulum.Date]:
        """
        Generate last day of subscription.

        Extra day is removed from end time, so end day will be *last* day of
        subscription. For example if granularity is one month,
        and is rounded at start of month, for january end day will be 31.
        If granularity is one day, and duration is one day - end day
        will be same as start day.

        :param start_date: date of subscription beginning
        """
        rounded_start_date = self.start_date(start_date)
        end = None

        if self.duration_type == GRANULARITY.DAY:
            end = rounded_start_date.add(days=self.duration)
        elif self.duration_type == GRANULARITY.WEEK:
            end = rounded_start_date.add(weeks=self.duration)
        elif self.duration_type == GRANULARITY.MONTH:
            end = rounded_start_date.add(months=self.duration)
        elif self.duration_type == GRANULARITY.YEAR:
            end = rounded_start_date.add(years=self.duration)

        if end:
            return end.add(days=-1)

        return None

    def events_to_date(
        self, *,
        to_date: date,
        from_date: date = None,
        filter_runner: Callable[[Event], bool] =
        SubscriptionsTypeEventFilter.ACTIVE
    ) -> List[Event]:
        """
        Get list of all events that can be visited by this subscription type
        Event are sorted by date.

        :param to_date: End date of calendar
        :param from_date: Start date of calendar, if not provided date.today()
        will be used
        :param filter_runner: Filter event for given criteria. Default criteria
        select only active events.

        :return: List of all events
        """
        return sorted(
            filter(
                filter_runner,
                [
                    e for x in self.event_class.all()
                    for e in
                    x.get_calendar(from_date or date.today(), to_date).values()
                ]
            ),
            key=lambda x: x.date
        )

    @property
    def duration_postfix(self):
        return pluralize(
            *GRANULARITY.for_value(self.duration_type).pluralize,
            self.duration
        )

    @staticmethod
    def get_absolute_url():
        return reverse('crm:manager:subscription:list')


class ClientManager(ScrmSafeDeleteManager):

    def with_active_subscription_to_event(self, event: Event) -> TenantQuerySet:
        cs = (
            ClientSubscriptions.objects
                .active_subscriptions_to_event(event)
                .order_by('client_id')
                # .distinct('client_id')
                .values_list('client_id', flat=True)
        )
        return self.get_queryset().filter(id__in=cs)


@reversion.register()
class Client(ScrmSafeDeleteModel, CompanyObjectModel):
    """Клиент-Ученик. Контактные данные. Баланс"""
    name = models.CharField("Имя", max_length=100)
    address = models.CharField("Адрес", max_length=255, blank=True)
    birthday = models.DateField("Дата рождения", null=True, blank=True)
    phone_number = PhoneNumberField("Телефон", blank=True)
    email_address = models.CharField("Email", max_length=50, blank=True)
    additional_info = models.TextField("Дополнительная информация", blank=True)

    vk_user_id = models.IntegerField("id ученика в ВК", null=True, blank=True)
    balance = models.DecimalField(
        "Баланс",
        max_digits=9,
        decimal_places=2,
        default=0
    )
    qr_code = models.UUIDField(
        "QR код",
        blank=True,
        null=True,
        unique=True,
        default=uuid.uuid4
    )

    objects = ClientManager()

    class Meta:
        unique_together = ('company', 'name')

    def get_absolute_url(self):
        return reverse('crm:manager:client:detail', kwargs={'client_id': self.pk})

    def last_sub(self, with_deleted=False):
        qs = self.clientsubscriptions_set.exclude_onetime()

        if not with_deleted:
            qs = qs.filter(subscription__deleted__isnull=True)

        return qs.order_by('-purchase_date').first()

    def last_attendance(self):
        return self.attendance_set.filter(marked=True).order_by('-event__date').first()

    def get_active_sub(self):
        return self.clientsubscriptions_set.select_related('subscription').active_subscriptions()

    def __str__(self):
        return self.name

    @property
    def vk_message_token(self) -> str:
        return self.company.vk_access_token

    def update_balance(self, top_up_amount, skip_notification: bool = False):
        """
        :param top_up_amount: Amount of added or removed from balance
        :param skip_notification: Prevent double notification send if buy sub
        """
        self.balance = self.balance + decimal.Decimal(top_up_amount)
        self.save()
        if not skip_notification:
            from gcp.tasks import enqueue
            enqueue('notify_client_balance', self.id)

    def add_balance_in_history(
        self,
        top_up_amount: float,
        reason: str,
        skip_notification: bool = False,
        changed_by: User = None
    ):
        """
        :param top_up_amount: Amount of added or removed from balance
        :param reason: Reason of client balance modification
        :param skip_notification: Prevent double notification send if buy sub
        :param changed_by: User changed balance
        """
        with transaction.atomic():
            ClientBalanceChangeHistory.objects.create(
                change_value=top_up_amount,
                client=self,
                reason=reason,
                changed_by=changed_by,
            )
            self.update_balance(top_up_amount, skip_notification)

    def signup_for_event(self, event: Event):
        with transaction.atomic():
            if not event.id:
                event.save()
            Attendance.objects.update_or_create(
                event=event,
                client=self,
                signed_up=True
            )

    def cancel_signup_for_event(self, event):
        with transaction.atomic():
            attendance = Attendance.objects.get(client=self, event=event)
            if attendance.subscription and attendance.marked:
                attendance.subscription.restore_visit()
            attendance.delete()

    def mark_visit(self, event, subscription: ClientSubscriptions):
        subscription.mark_visit(event)

    def restore_visit(self, event):
        attendance = Attendance.objects.get(client=self, event=event)
        attendance.restore_visit()


class ClientSubscriptionQuerySet(TenantQuerySet):
    def active_subscriptions_to_event(self, event: Event):
        """Get all active subscriptions for selected event"""
        return self.annotate(
            counted_visits_left=F('visits_on_by_time') - Count(
                'attendance',
                filter=Q(attendance__event__date__lt=event.date) &
                       Q(attendance__subscription_id=F('id'))
            )
        ).filter(
            subscription__event_class=event.event_class,
            start_date__lte=event.date,
            end_date__gte=event.date,
            counted_visits_left__gt=0
        )

    def active_subscriptions_to_date(self, to_date: date):
        """
        Get all subscriptions, active at particular date

        :param to_date: Date to test activity
        :return:
        """
        return self.annotate(
            counted_visits_left=F('visits_on_by_time') - Count(
                'attendance',
                filter=Q(attendance__event__date__lt=to_date) &
                       Q(attendance__subscription_id=F('id'))
            )
        ).filter(
            start_date__lte=to_date,
            end_date__gte=to_date,
            counted_visits_left__gt=0
        )

    def active_subscriptions(self):
        today = date.today()
        return self.filter(
            start_date__lte=today,
            end_date__gte=today,
            visits_left__gt=0
        ) | self.filter(
            visits_left=1,
            start_date=today,
            end_date=today,
            subscription__one_time=True,
        )


class ClientSubscriptionsManager(
    ScrmTenantManagerMixin,
    BaseManager.from_queryset(ClientSubscriptionQuerySet)
):
    def active_subscriptions_to_event(self, event: Event):
        return self.get_queryset().active_subscriptions_to_event(event)

    def active_subscriptions_to_date(self, to_date: date):
        return self.get_queryset().active_subscriptions_to_date(to_date)

    def active_subscriptions(self):
        return self.get_queryset().active_subscriptions()

    def extend_by_cancellation(self, cancelled_event: Event):
        for subscription in self.active_subscriptions_to_event(cancelled_event):
            subscription.extend_by_cancellation(cancelled_event)

    def revoke_extending(self, activated_event: Event):
        # Don't try revoke on non-active events or non-canceled evens
        if not activated_event.is_active or \
            not activated_event.is_canceled or \
            not activated_event.canceled_with_extending:
            return

        subs_ids = activated_event.extensionhistory_set.all().values_list(
            'client_subscription_id', flat=True)

        for subscription in self.get_queryset().filter(id__in=subs_ids):
            subscription.revoke_extending(activated_event)

    def exclude_onetime(self):
        return self.get_queryset().filter(subscription__one_time=False)


class ClientAttendanceExists(Exception):
    pass


@reversion.register()
class ClientSubscriptions(CompanyObjectModel):
    """Абонементы клиента"""
    client = TenantForeignKey(
        Client,
        on_delete=models.PROTECT,
        verbose_name="Ученик")
    subscription = TenantForeignKey(
        SubscriptionsType,
        on_delete=models.PROTECT,
        verbose_name="Тип Абонемента")
    event = TenantForeignKey(
        'Event',
        on_delete=models.PROTECT,
        verbose_name="Продан на тренировке",
        null=True,
        blank=True,
    )
    sold_by = TenantForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Кто продал",
        null=True,
    )
    purchase_date = models.DateField("Дата покупки", default=date.today)
    start_date = models.DateField("Дата начала", default=date.today)
    end_date = models.DateField(null=True)
    price = models.FloatField("Стоимость")
    visits_on_by_time = models.PositiveSmallIntegerField(
        "Количество визитов на момент покупки"
    )
    visits_left = models.PositiveIntegerField("Остаток посещений")

    objects = ClientSubscriptionsManager()

    def visits_to_date(self, to_date: date):
        """
        Получить остаток посещений на указанную дату.

        Данные формируются исходя из реального количества посещений, на
        указанную дату, включая её. Если проверка идет до 01.06.2019, то
        посещения за эту дату, также будут включены в расчет.

        Если запрашиваемая даты - указана раньше чем начало абонемента, то
        остаток будет равен нулю.

        :param to_date: Дата, включительно до котрой нужно рассчитать остаток
        :return: Количество оставщихся посещений
        """
        if to_date < self.start_date:
            return 0

        return self.visits_on_by_time - self.attendance_set.filter(
            event__date__lte=to_date
        ).count()

    @property
    def max_visits_to_add(self):
        """
        Максимальное количество посещений, которое можно использовать при
        продлении

        :return: Число посещений на текущую дату.
        """
        today = date.today()
        return self.visits_to_date(today) - self.normalized_visits_left

    @property
    def normalized_visits_left(self):
        """
        Нормальзованное значение оставщихся визитов. Суть нормализации
        заключается в последовательном уменьшении оставшихся визитов,
        при истичении срока абонеента.

        Если на абонементе осталось 10 занятий, а исходя из календаря
        можно отходить только 8, то нормализованное значение и будет 8.
        Если же а абонементе осталось 10 занятий, а по расписанию можно отходить
        12, то нормализованное значение будет равно текущему остатку - 10

        :return: Число посещений
        """
        today = date.today()
        return min(
            self.visits_to_date(today),
            len(self.subscription.events_to_date(
                from_date=today + timedelta(days=1),
                to_date=self.end_date
            ))
        )

    def save(self, *args, **kwargs):
        # Prevent change end date for extended client subscription
        if not self.id:
            self.start_date = self.subscription.start_date(self.start_date)
            self.end_date = self.subscription.end_date(self.start_date)
            # Save original provided client visits limit
            self.visits_on_by_time = self.visits_left

        super().save(*args, **kwargs)

    def next_event_date(
        self,
        start_date: date,
        visits_to_add: int
    ):
        days = list(
            DayOfTheWeekClass.objects
            .filter(
                event_id__in=self.subscription.event_class.only('id')
            )
            .order_by('day', 'start_time', 'end_time')
            .values_list('day', flat=True)
        )
        if len(days) == 0:
            return start_date

        last_day = start_date.weekday()
        # Персортировываем дни занятий, так чтоб день текущего последнего
        # занятия был в конце списка.
        if days[-1] != last_day:
            for idx, day in enumerate(days):
                if day > last_day:
                    break

            days = days[idx:] + days[:idx]

        deltas = extend_range_distance(days, last_day)

        add_days = 0
        # Если посещений добавлено больше чем всего занятий в неделю,
        # значит абонемент продляется на Х недель
        if visits_to_add > len(days):
            add_days = 7 * (visits_to_add // len(days))

        # Ищем дистанцю между последним занятием и наименьшим возможным
        # и добавляем это к дате продления абонемента
        d_idx = (visits_to_add % len(days)) - 1
        d_idx = d_idx if d_idx >= 0 else len(days) - 1
        add_days += deltas[d_idx]

        return start_date + timedelta(days=add_days)

    def extend_duration(self, visits_limit: int, reason: str = ''):
        # Нельзя продлять разовые абонементы
        if self.subscription.one_time:
            return

        today = date.today()
        # Если абонемент закончился - то просто растягиваем абонемент на
        # добавляемое количество дней
        if self.end_date < today:
            new_end_date = self.next_event_date(
                today, self.overlapping_count(
                    visits_limit, start_date=today + timedelta(days=1)
                )
            )
            new_visits_limit = visits_limit
        # Если при добавлении в абонемент занятий, происходит выход за пределы
        # абонемента - то необхдимо добавить дополнительные дни
        else:
            # Пересчитываем
            recalc_visits_left = self.normalized_visits_left
            new_visits_limit = recalc_visits_left + visits_limit
            if self.is_overlapping_with_amount(
                recalc_visits_left + visits_limit,
                start_date=today + timedelta(days=1)
            ):
                # Дата от которой отсчитываем продления нужно брать
                # либо от последний даты абонемента, если он ещё не просрочен
                # либо от текущий даты - если абонемент просрочен.
                # Вариант с текущей датой - это случаи когда абонементы
                # продляют по болезни
                last_visit_date = max(self.end_date, today)
                new_end_date = self.next_event_date(
                    last_visit_date, self.overlapping_count(
                        recalc_visits_left + visits_limit,
                        start_date=today + timedelta(days=1)
                    )
                )
            else:
                new_end_date = self.end_date

        # Дата окончания не менялась, и количество продляемых занятий меньше
        # чем реально можно отходить по остатку то ничего не делаем
        if new_end_date == self.end_date and visits_limit == 0:
            return

        with transaction.atomic():
            ExtensionHistory.objects.create(
                client_subscription=self,
                reason=reason,
                added_visits=visits_limit,
                extended_from=(
                    self.end_date if new_end_date != self.end_date else None
                ),
                extended_to=(
                    new_end_date if new_end_date != self.end_date else None
                )
            )
            self.visits_left = new_visits_limit
            self.end_date = new_end_date
            self.save()
            from gcp.tasks import enqueue
            enqueue('notify_client_subscription_extend', self.id)

    def extend_by_cancellation(self, cancelled_event: Event):
        possible_extension_date = self.nearest_extended_end_date(
            cancelled_event.event_class)

        if possible_extension_date == self.end_date:
            # Don't extend if there is no more future events for this
            # event class
            return

        with transaction.atomic():
            ExtensionHistory.objects.create(
                client_subscription=self,
                reason=f'В связи с отменой тренировки {cancelled_event}',
                added_visits=0,
                related_event=cancelled_event,
                extended_from=self.end_date,
                extended_to=possible_extension_date
            )

            self.end_date = possible_extension_date
            self.save()

    def revoke_extending(self, activated_event: Event):
        extension_to_delete = (
            activated_event.extensionhistory_set
                .filter(client_subscription=self)
                .order_by('date_extended')
                .first()
        )
        if not extension_to_delete:
            # Nothing to delete
            return

        extending_chain = ExtensionHistory.objects.filter(
            client_subscription=self,
            date_extended__gt=extension_to_delete.date_extended
        )

        # If we have any extension history AFTER removable,
        # we must rebuild history date changing
        # Set current extension history dates to next extension history item
        # and so further.
        # Last extension history extended_from will be used as real date,
        # on which will be truncated client subscription
        # If there is empty chain, it means that extension history is last one
        # and no history rebuilding needed
        prev_from = extension_to_delete.extended_from
        prev_to = extension_to_delete.extended_to
        with transaction.atomic():
            for chained_extension in extending_chain:
                current_from = chained_extension.extended_from
                current_to = chained_extension.extended_to

                chained_extension.extended_from = prev_from
                chained_extension.extended_to = prev_to
                chained_extension.save()

                prev_from = current_from
                prev_to = current_to

            if prev_from:
                self.end_date = prev_from
                self.save()
            else:
                logger.error(
                    'Subscription date extension with empty extended_from found'
                )

            extension_to_delete.delete()

    def nearest_extended_end_date(self, event_class: EventClass = None):
        possible_events = self.subscription.event_class.filter(
            Q(date_to__isnull=True) | Q(date_to__gt=self.end_date)
        )

        if event_class:
            possible_events = possible_events.filter(id=event_class.id)

        if not possible_events.exists():
            return self.end_date

        new_end_date = list(filter(bool, [
            x.get_nearest_event_to_or_none(self.end_date)
            for x in possible_events
        ]))

        return min(new_end_date) if len(new_end_date) else self.end_date

    def is_extended(self):
        return self.extensionhistory_set.exists()

    def get_absolute_url(self):
        return reverse(
            'crm:manager:client:detail', kwargs={'pk': self.client.id})

    def remained_events(self) -> List[Event]:
        """
        Return list of remained events from today until end date. With care
        about left visits.

        :return: List of all events that can be visited one after one,
        by this client subscription
        """
        return (
            self.subscription
                .events_to_date(to_date=self.end_date)[:self.visits_left]
        )

    def is_overlapping_with_amount(
        self,
        visits_amount: int,
        start_date: Optional[date] = None
    ) -> bool:
        """
        Return information that client subscription allows visit more events
        than are planned

        :param visits_amount: Amount of visits that can be used
        :param start_date: Дата, от которой надо проверить выход посещений
        за пределы абонемента
        :return: True if after visiting all events from calendar will remain
        some visits on this subscription
        """
        from_date = self.start_date if start_date is None else start_date
        try:
            return len(self.subscription.events_to_date(
                from_date=from_date, to_date=self.end_date
            )) < visits_amount
        except ValueError:
            return False

    def overlapping_count(
        self,
        visits_amount: int,
        start_date: Optional[date] = None
    ) -> int:
        """
        Получить количество занятий, которое останется на абонементе, после
        окончания срока действия

        :param visits_amount: Количесто текущих доступных посещений
        :param start_date: Дата, от которой надо проверить выход посещений
        за пределы абонемента
        :return: Остаток занятий, если ходить на каждое доступное занятие
        """
        from_date = self.start_date if start_date is None else start_date

        return visits_amount - (
            len(self.subscription.events_to_date(
                from_date=from_date, to_date=self.end_date
            ))
        )

    def is_overlapping(self) -> bool:
        """
        Return information that client subscription allows visit more events
        than are planned

        :return: True if after visiting all events from calendar will remain
        some visits on this subscription
        """
        return self.is_overlapping_with_amount(self.visits_left)

    def is_overlapping_with_cancelled(self) -> bool:
        """
        Return information that client subscription allows visit more events
        than are planned, event with canceled events

        :return: True if after visiting all events from calendar will remain
        some visits on this subscription. And this quantity of remaining
        canceled events is greater that remaining visits minus active events
        """
        try:
            return len(self.subscription.events_to_date(
                from_date=self.start_date,
                to_date=self.end_date,
                filter_runner=SubscriptionsTypeEventFilter.ALL
            )) < self.visits_left
        except ValueError:
            return False

    def canceled_events(
        self,
        from_date: date = None,
        to_date: date = None
    ) -> List[Event]:
        try:
            return self.subscription.events_to_date(
                from_date=from_date or self.start_date,
                to_date=to_date or self.end_date,
                filter_runner=SubscriptionsTypeEventFilter.CANCELED
            )
        except ValueError:
            return []

    def last_visited_event(self):
        last = self.attendance_set.select_related('event').filter(
            marked=True,
            event__canceled_at__isnull=True,
        ).exclude(
            event__date__gt=date.today()
        ).order_by('-event__date').first()
        if last:
            return last.event

    def canceled_events_count(self):
        return len(self.canceled_events())

    def is_active_at_date_without_events(self, check_date) -> bool:
        """
        Check if client subscription is active at particular date.
        It's simple check, without events investigation. Check only if
        client subscription have some visits left, and date is in allowed
        rage.

        This function can be used when we need check some attendance for
        past date.

        :param check_date: what date we check
        :return: is active subscription at date or not
        """
        return (
            self.start_date <= check_date <= self.end_date and
            self.visits_left > 0
        )

    def is_active_to_date(self, to_date: date) -> bool:
        """
        Check if current client subscription is valid until some date.

        This check is performed only from current day to future date. It all
        because we check current visits limit, and calculations about "how
        much visits was on some past date" ignored.

        :param to_date: until what date check activity
        :return: is active client subscription or not
        """
        if not self.is_active_at_date_without_events(to_date):
            return False

        # Extract one day - to check if subscriptions ends before date
        future_events = self.subscription.events_to_date(
            to_date=(to_date - timedelta(days=1)))

        # If visits limit ends before date, we are sure that subscription is
        # no more active
        return not (self.visits_left - len(future_events) <= 0)

    def is_active(self) -> bool:
        return self.is_active_to_date(date.today())

    @property
    def is_expiring(self) -> bool:
        delta = self.end_date - date.today()
        return delta.days <= 7 or self.visits_left == 1

    def mark_visit(self, event):
        """Отметить посещение по абонементу"""
        if not self.is_active_at_date_without_events(event.date):
            raise ValueError('Subscription or event is incorrect')

        with transaction.atomic():
            attendance, created = Attendance.objects.get_or_create(
                event=event,
                client=self.client,
                defaults={'subscription': self, 'marked': False})

            if not created and attendance.marked:
                raise ClientAttendanceExists(
                    'Client attendance for this event already exists')

            attendance.mark_visit(self)
            self.visits_left = self.visits_left - 1
            self.save()
            from gcp.tasks import enqueue
            enqueue('notify_client_subscription_visit', self.id)

    def restore_visit(self):
        with transaction.atomic():
            self.visits_left = self.visits_left + 1
            self.save()
            from gcp.tasks import enqueue
            enqueue('notify_client_subscription_visit', self.id)

    class Meta:
        ordering = ['purchase_date']

    def __str__(self):
        return f'{self.subscription.name} (до {self.end_date:%d.%m.%Y})'


class ClientBalanceChangeHistory(CompanyObjectModel):
    change_value = models.DecimalField(
        "Сумма изменения баланса",
        max_digits=9,
        decimal_places=2
    )
    client = TenantForeignKey(
        Client,
        on_delete=models.PROTECT,
        verbose_name="Ученик"
    )
    reason = models.TextField(
        "Причина изменения баланса",
        blank=True
    )
    changed_by = TenantForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Кто изменил",
        null=True
    )
    subscription = TenantForeignKey(
        ClientSubscriptions,
        on_delete=models.PROTECT,
        blank=True,
        verbose_name="Абонемент Клиента",
        null=True,
        default=None
    )
    entry_date = models.DateTimeField(
        "Дата зачисления",
        default=timezone.now
    )


@reversion.register()
class ExtensionHistory(CompanyObjectModel):
    client_subscription = TenantForeignKey(
        ClientSubscriptions,
        on_delete=models.PROTECT,
        verbose_name='Абонемент клиента')
    date_extended = models.DateTimeField(
        'Дата продления',
        default=timezone.now)
    reason = models.CharField('Причина продления', max_length=255, blank=False)
    related_event = TenantForeignKey(
        to='Event',
        on_delete=models.PROTECT,
        null=True
    )
    added_visits = models.IntegerField("Добавлено посещений")
    extended_from = models.DateField(
        'Абонеметы был продлен с',
        blank=True,
        null=True
    )
    extended_to = models.DateField(
        'Абонемент продлен до дня',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['date_extended']


class EventManager(TenantManagerMixin, models.Manager):
    def get_or_virtual(self, event_class_id: int, event_date: date) -> Event:
        try:
            return self.get(event_class_id=event_class_id, date=event_date)
        except Event.DoesNotExist:
            event_class = get_object_or_404(EventClass, id=event_class_id)
            return Event(date=event_date, event_class=event_class)


@reversion.register()
class Event(CompanyObjectModel):
    """Конкретное мероприятие (тренировка)"""
    # TODO: Валидацию по event_class
    date = models.DateField("Дата")
    event_class = TenantForeignKey(
        EventClass,
        on_delete=models.PROTECT,
        verbose_name="Тренировка"
    )
    canceled_at = models.DateField('Дата отмены тренировки', null=True)
    canceled_with_extending = models.BooleanField(
        'Отмена была с продленим абонемента?',
        default=False
    )
    is_closed = models.BooleanField(
        'Тренировка закрыта',
        default=False
    )

    objects = EventManager()

    class Meta:
        unique_together = ('event_class', 'date',)

    def clean(self):
        # Проверяем пренадлижит ли указанная дата тренировке
        # TODO: Refactor dump Event.is_event_day
        if not self.event_class.is_event_day(self.date):
            raise ValidationError({"date": "Дата не соответствует тренировке"})

    @property
    def signed_up_clients(self):
        """
        Return amount of clients signed for one event. Use only in case when
        we work only with one event. For grouped operations better use optimized
        queries with annotate and values

        :return: Amount of clients signed up for event
        """
        return self.attendance_set.filter(signed_up=True).count()

    def get_present_clients_count(self):
        # Получаем количество посетивших данную тренировку клиентов
        return self.attendance_set.filter(marked=True).count()

    def get_clients_count_one_time_sub(self):
        # Получаем количество посетивших данную тренировку
        # по одноразовому абонементу
        queryset = ClientSubscriptions.objects.filter(
            subscription__one_time=True,
            event=self,
        )
        return queryset.count()

    def get_subs_sales(self):
        # Получаем количество проданных абонементов
        queryset = ClientSubscriptions.objects.filter(
            subscription__one_time=False,
            event=self
        )
        return queryset.count()

    def get_profit(self):
        # Получаем прибыль
        price = ClientSubscriptions.objects.filter(
            event=self
        ).aggregate(Sum('price'))

        return price['price__sum'] or 0

    def __str__(self):
        return f'{self.date:"%Y-%m-%d"} {self.event_class}'

    @property
    def is_virtual(self):
        return self.id is None

    @property
    def is_canceled(self):
        return self.canceled_at is not None

    @property
    def is_active(self):
        return self.date >= date.today()

    @property
    def is_non_editable(self):
        return self.is_canceled or self.is_closed

    @property
    def is_overpast(self):
        return self.date <= date.today()

    # Hack to cache event class name in useful cases
    # Usage can be seen in EventClass.get_calendar
    _ec_name: str = None
    _start_time: time = None
    _end_time: time = None

    @property
    def event_class_name(self) -> str:
        return self._ec_name if self._ec_name else self.event_class.name

    @event_class_name.setter
    def event_class_name(self, val):
        self._ec_name = val

    @property
    def start_time(self):
        if self._start_time:
            return self._start_time

        weekday = self.date.weekday()
        start_time = self.event_class.dayoftheweekclass_set.filter(
            day=weekday
        ).first().start_time
        return start_time

    @start_time.setter
    def start_time(self, val):
        self._start_time = val

    @property
    def end_time(self):
        if self._end_time:
            return self._end_time

        weekday = self.date.weekday()
        end_time = self.event_class.dayoftheweekclass_set.filter(
            day=weekday
        ).first().end_time
        return end_time

    @end_time.setter
    def end_time(self, val):
        self._end_time = val

    def cancel_event(self, extend_subscriptions=False):
        if not self.is_active:
            raise ValueError("Event is outdated. It can't be canceled.")

        if self.is_canceled:
            raise ValueError("Event is already cancelled.")

        with transaction.atomic():
            self.canceled_at = date.today()
            self.canceled_with_extending = extend_subscriptions
            self.save()

            if extend_subscriptions:
                ClientSubscriptions.objects.extend_by_cancellation(self)

            try:
                from gcp.tasks import enqueue
                enqueue('notify_event_cancellation', self.id)
            except ImportError:
                pass

    def activate_event(self, revoke_extending=False):
        if not self.is_active:
            raise ValueError("Event is outdated. It can't be activated.")

        if not self.is_canceled:
            raise ValueError("Event is already in action.")

        original_cwe = self.canceled_with_extending
        with transaction.atomic():
            self.canceled_at = None
            self.canceled_with_extending = False
            self.save()

            if revoke_extending and original_cwe:
                ClientSubscriptions.objects.revoke_extending(self)

    def close_event(self):
        """Закрыть тренировку"""
        if not self.is_overpast:
            raise ValueError("Event for future date, can't be closed")

        if self.is_closed:
            raise ValueError("Event is already closed")

        self.is_closed = True
        self.save()
        from gcp.tasks import enqueue
        enqueue('notify_manager_event_closed', self.id)

    def open_event(self):
        """Открыть тренировку"""
        if not self.is_closed:
            raise ValueError("Event is already opened")

        self.is_closed = False
        self.save()
        from gcp.tasks import enqueue
        enqueue('notify_manager_event_opened', self.id)


@reversion.register()
class Attendance(CompanyObjectModel):
    """Посещение клиентом мероприятия(тренировки)"""
    client = TenantForeignKey(
        Client,
        on_delete=models.PROTECT,
        verbose_name="Ученик"
    )
    event = TenantForeignKey(
        Event,
        on_delete=models.PROTECT,
        verbose_name="Тренировка"
    )
    subscription = TenantForeignKey(
        ClientSubscriptions,
        on_delete=models.PROTECT,
        blank=True,
        verbose_name="Абонемент Клиента",
        null=True,
        default=None
    )

    marked = models.BooleanField(
        'Присутствовал на мероприятии',
        default=False
    )
    signed_up = models.BooleanField(
        'Записан на мероприятие',
        default=False
    )

    def mark_visit(self, subscription: ClientSubscriptions):
        self.subscription = subscription
        self.marked = True
        self.save()

    def restore_visit(self):
        with transaction.atomic():
            self.marked = False
            if self.subscription:
                self.subscription.restore_visit()
            self.save()

    class Meta:
        unique_together = ('client', 'event',)

    def __str__(self):
        return f'{self.client} {self.event}'
