from __future__ import annotations

from datetime import date, datetime, timedelta
from itertools import count
from typing import Dict, List, Optional

import reversion
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction, utils
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django_multitenant.fields import TenantForeignKey
from django_multitenant.mixins import TenantManagerMixin
from django_multitenant.models import TenantModel
from django_multitenant.utils import get_current_tenant
from psycopg2 import Error as Psycopg2Error
from safedelete.models import SafeDeleteModel
from transliterate import translit

from crm.events import get_nearest_to, next_day, Weekdays

INTERNAL_COMPANY = 'INTERNAL'


class NoFutureEvent(Exception):
    pass


@reversion.register()
class Company(models.Model):
    """Компания. Multitentant строится вокруг этой модели"""

    # Внутренее поле, нужное для работы административных аккаунтов
    # По факту является своеобразным uuid
    name = models.CharField("Название", max_length=100, unique=True)
    display_name = models.CharField('Отображаемое название', max_length=100)
    tenant_id = 'id'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        for idx in count(start=1):
            trans_name = translit(
                self.display_name, language_code='ru', reversed=True)
            name = trans_name.replace(' ', '_').lower()
            inner_name = f'{idx}_{name}'[:100]
            if not Company.objects.filter(name=inner_name).exists():
                self.name = inner_name
                break

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.display_name


class CustomUserManager(TenantManagerMixin, UserManager):
    def generate_uniq_username(self, first_name, last_name, prefix='user'):
        for idx in count():
            trans_f = translit(first_name, language_code='ru', reversed=True)
            trans_l = translit(last_name, language_code='ru', reversed=True)
            name = f'{prefix}_{idx}_{trans_f}_{trans_l}'.lower()[:150]
            if not self.filter(username=name).exists():
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
            return Company.objects.get(name=INTERNAL_COMPANY)
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
        return self.vk_data('id')

    @property
    def vk_link(self) -> Optional[str]:
        vkid = self.vk_id
        return 'https://vk.com/id{}'.format(vkid) if vkid else None

    def vk_data(self, data_key: str) -> Optional[str]:
        try:
            social = self.social_auth.get(provider='vk-oauth2')
        except models.ObjectDoesNotExist:
            return None

        return social.extra_data.get(data_key)


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
class Location(SafeDeleteModel, CompanyObjectModel):
    name = models.CharField("Название", max_length=100)
    address = models.CharField("Адрес", max_length=1000, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('crm:manager:locations:list')


@reversion.register()
class Coach(SafeDeleteModel, CompanyObjectModel):
    """
    Профиль тренера
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    phone_number = models.CharField("Телефон", max_length=50, blank=True)

    def __str__(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return reverse('crm:manager:coach:detail', kwargs={'pk': self.pk})

    @property
    def has_active_events(self):
        today = timezone.now().date()
        return self.eventclass_set.filter(
            Q(date_from__gt=today) |
            Q(date_to__gt=today)
        ).exists()


@reversion.register()
class Manager(CompanyObjectModel):
    """
    Профиль менеджера
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)

    def __str__(self):
        return self.user.get_full_name()


@reversion.register()
class EventClass(CompanyObjectModel):
    """
    Описание шаблона мероприятия (Класс вид).
    Например, тренировки в зале бокса у Иванова по средам и пятницам
    """
    name = models.CharField("Название", max_length=100)
    location = TenantForeignKey(
        Location,
        on_delete=models.PROTECT,
        verbose_name="Расположение")
    coach = TenantForeignKey(
        Coach,
        on_delete=models.PROTECT,
        verbose_name="Тренер")
    date_from = models.DateField("Дата с", null=True, blank=True)
    date_to = models.DateField("Дата по", null=True, blank=True)

    def days(self) -> List[int]:
        """
        Get list of all weekdays of current event

        For example: [0, 2, 4] for monday, wednesday, friday
        """
        days = list(
            self.dayoftheweekclass_set.all().values_list('day', flat=True))

        if not len(days):
            raise ValueError("Event class don't have any days to spread")

        return days

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
            return self.get_nearest_day_or_none(required_day)
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
        events = {
            event.date: event
            for event in
            self.event_set.filter(date__range=(start_date, end_date))
        }
        # Решение влоб - перебор всех дней с проверкой входят
        # ли они в календарь.
        # TODO: переписать на генератор(yield) -
        #  EventClass может возвращать следующий день исходя из настроек
        for n in range(int((end_date - start_date).days)):
            curr_date = start_date + timedelta(n)
            if curr_date not in events:
                if self.is_event_day(curr_date):
                    events[curr_date] = Event(date=curr_date, event_class=self)

        return events

    def get_calendar_gen(
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
        events = {
            event.date: event
            for event in
            self.event_set.filter(date__range=(start_date, end_date))
        }
        for event_date in next_day(start_date, end_date, Weekdays(self.days())):
            if event_date not in events:
                events[event_date] = Event(date=event_date, event_class=self)

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
        default=timezone.now
    )
    end_time = models.TimeField(
        "Время окнчания тренировки",
        default=timezone.now
    )

    class Meta:
        unique_together = ('day', 'event',)


granularity = (
    ('day', 'День'),
    ('week', 'Неделя'),
    ('month', 'Месяц'),
    ('year', 'Год')
)


@reversion.register()
class SubscriptionsType(SafeDeleteModel, CompanyObjectModel):
    """
    Типы абонементов
    Описывает продолжительность действия, количество посещений,
    какие тренировки позволяет посещать
    """
    name = models.CharField("Название", max_length=100)
    price = models.FloatField("Стоимость")
    duration_type = models.CharField(
        "Временные рамки абонемента",
        max_length=20,
        choices=granularity,
        default=granularity[0]
    )
    duration = models.PositiveIntegerField("Продолжительность")
    rounding = models.BooleanField(
        "Округление начала действия абонемента",
        default=False
    )
    visit_limit = models.PositiveIntegerField("Количество посещений")
    event_class = models.ManyToManyField(
        EventClass,
        verbose_name="Допустимые тренировки"
    )

    def __str__(self):
        return 'name: (0)'.format(self.name)

    def get_start_date(self, rounding_date):
        """
        Возвращает дату начала действия абонемента после округления.
        rounding_date - дата начала действия абонемента до округления
        """
        if self.rounding:
            weekday = rounding_date.weekday()
            if self.duration_type == granularity[0][0]:
                start_date = rounding_date
            elif self.duration_type == granularity[1][0]:
                start_date = rounding_date - timedelta(weekday)
            elif self.duration_type == granularity[2][0]:
                start_date = datetime(
                    rounding_date.year, rounding_date.month, 1)
            elif self.duration_type == granularity[3][0]:
                start_date = datetime(rounding_date.year, 1, 1)
        else:
            start_date = rounding_date
        return start_date

    def get_end_date(self, start_date):
        """
        Возвращает дату окончания действия абонемента.
        start_date - дата начала действия абонемента
        """
        end_date = None
        if self.duration_type == granularity[0][0]:
            end_date = start_date + relativedelta(days=self.duration)
        elif self.duration_type == granularity[1][0]:
            end_date = start_date + relativedelta(days=6 * self.duration)
        elif self.duration_type == granularity[2][0]:
            end_date = start_date + relativedelta(months=self.duration)
        elif self.duration_type == granularity[3][0]:
            end_date = start_date + relativedelta(years=self.duration)
        return end_date

    @staticmethod
    def get_absolute_url():
        return reverse('crm:manager:subscription:list')


@reversion.register()
class Client(CompanyObjectModel):
    """Клиент-Ученик. Котнактные данные. Баланс"""
    name = models.CharField("Имя",
                            max_length=100)
    address = models.CharField("Адрес",
                               max_length=255,
                               blank=True)
    birthday = models.DateField("Дата рождения",
                                null=True,
                                blank=True)
    phone_number = models.CharField("Телефон",
                                    max_length=50,
                                    blank=True)
    email_address = models.CharField("Email",
                                     max_length=50,
                                     blank=True)
    vk_user_id = models.IntegerField("id ученика в ВК",
                                     null=True,
                                     blank=True)
    balance = models.FloatField("Баланс",
                                default=0)

    class Meta:
        unique_together = ('company', 'name')

    def get_absolute_url(self):
        return reverse('crm:manager:client:detail', kwargs={'pk': self.pk})

    @property
    def last_sub(self):
        return self.clientsubscriptions_set.order_by('purchase_date').first

    def __str__(self):
        return self.name


@reversion.register()
class ClientSubscriptions(CompanyObjectModel):
    """Абонементы клиента"""
    client = TenantForeignKey(Client,
                              on_delete=models.PROTECT,
                              verbose_name="Ученик")
    subscription = TenantForeignKey(SubscriptionsType,
                                    on_delete=models.PROTECT,
                                    verbose_name="Тип Абонемента")
    purchase_date = models.DateTimeField("Дата покупки", default=timezone.now)
    start_date = models.DateTimeField("Дата начала", default=timezone.now)
    end_date = models.DateTimeField(null=True)
    price = models.FloatField("Стоимость")
    visits_left = models.PositiveIntegerField("Остаток посещений")

    def save(self, *args, **kwargs):
        self.start_date = self.subscription.get_start_date(self.start_date)
        self.end_date = self.subscription.get_end_date(self.start_date)
        super(ClientSubscriptions, self).save(*args, **kwargs)

    def extend_duration(self, added_visits, reason=''):
        with transaction.atomic():
            ExtensionHistory.objects.create(
                client_subscription=self,
                reason=reason,
                added_visits=added_visits
            )
            self.visits_left += int(added_visits)
            self.end_date = self.nearest_extended_end_date()
            self.save()

    def nearest_extended_end_date(self):
        possible_events = self.subscription.event_class.filter(
            Q(date_to__isnull=True) | Q(date_to__gt=self.end_date)
        )

        if not possible_events.exists():
            raise NoFutureEvent()

        new_end_date = list(filter(bool, [
            x.get_nearest_event_to_or_none(self.end_date)
            for x in possible_events
        ]))

        return min(new_end_date) if len(new_end_date) else self.end_date

    def get_absolute_url(self):
        return reverse(
            'crm:manager:client:detail', kwargs={'pk': self.client.id})

    def is_expiring(self):
        current_date = datetime.now(timezone.utc)
        end_date = self.end_date
        delta = end_date - current_date
        return delta.days <= 7 or self.visits_left == 1

    class Meta:
        ordering = ['purchase_date']


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
    # related_event = TenantForeignKey(
    #     to='Event',
    #     on_delete=models.PROTECT,
    #     null=True
    # )
    added_visits = models.PositiveIntegerField("Добавлено посещений")
    # extended_to = models.DateField(
    #     'Абонемент продлен до дня',
    #     blank=True,
    #     null=True
    # )

    class Meta:
        ordering = ['date_extended']


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
    # canceled_at = models.DateField('Дата отмены тренировки', null=True)

    class Meta:
        unique_together = ('event_class', 'date',)

    def clean(self):
        # Проверяем пренадлижит ли указанная дата тренировке
        if not self.event_class.is_event_day(self.date):
            raise ValidationError({"date": "Дата не соответствует тренировке"})

    def __str__(self):
        return f'{self.date:"%Y-%m-%d"} {self.event_class}'


@reversion.register()
class Attendance(CompanyObjectModel):
    """Посещение клиентом мероприятия(тренировки)"""
    client = TenantForeignKey(Client,
                              on_delete=models.PROTECT,
                              verbose_name="Ученик")
    event = TenantForeignKey(Event,
                             on_delete=models.PROTECT,
                             verbose_name="Тренировка")

    class Meta:
        unique_together = ('client', 'event',)

    def __str__(self):
        return self.client.name + " " + str(self.event)
