from datetime import date, datetime, timedelta
from itertools import count
from typing import Dict, Optional

from transliterate import translit

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from libs.django_multitenant.django_multitenant.fields import *
#from libs.django_multitenant.django_multitenant.mixins import *
from libs.django_multitenant.django_multitenant.models import TenantModel


class CustomUserManager(UserManager):
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
            first_name=first_name, last_name=last_name
        )


class User(AbstractUser):
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


class Company(models.Model):
    """Компания. Multitentant строится вокруг этой модели"""
    name = models.CharField("Название",
                            max_length=100)
    tenant_id = 'id'

    def __str__(self):
        return self.name


class CompanyObjectModel(TenantModel):
    """Абстрактный класс для разделяемых по компаниям моделей"""
    company = models.ForeignKey(Company,
                                on_delete=models.PROTECT)
    tenant_id = 'company_id'
    unique_together = ["id", "company"]

    class Meta:
        abstract = True


class Location(CompanyObjectModel):
    name = models.CharField("Название",
                            max_length=100)
    address = models.CharField("Адрес",
                               max_length=1000,
                               blank=True)

    def __str__(self):
        return self.name


class Coach(models.Model):
    """
    Профиль тренера
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)

    def __str__(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return reverse('crm:manager:coach:detail', kwargs={'pk': self.pk})


class Manager(CompanyObjectModel):
    """
    Профиль менеджера
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)

    def __str__(self):
        return self.user.get_full_name()


class EventClass(models.Model):
    """Описание мероприятия (Класс вид). Например, тренировки по средам и пятницам у новичков"""
    name = models.CharField("Название",
                            max_length=100)
    location = models.ForeignKey(Location,
                                 on_delete=models.PROTECT,
                                 verbose_name="Расположение")
    coach = models.ForeignKey(Coach,
                              on_delete=models.PROTECT,
                              verbose_name="Тренер"
                              )
    date_from = models.DateField("Дата с",
                                 null=True,
                                 blank=True)
    date_to = models.DateField("Дата по",
                               null=True,
                               blank=True)

    def is_event_day(self, day: date) -> bool:
        """Входит ли переданный день в мероприятия (есть ли в этот день тренировка) """

        # Проверяем, входит ли проверяемый день в диапазон проводимых тренировок
        if (self.date_from and self.date_from > day) or (self.date_to and self.date_to < day):
            return False

        # Проверяем, проходят ли в этот день недели тренировки
        weekdays = self.dayoftheweekclass_set.all();
        if weekdays:
            for weekday in weekdays:
                if weekday.day == day.weekday():
                    break
            else:
                return False # https://ncoghlan-devs-python-notes.readthedocs.io/en/latest/python_concepts/break_else.html

        return True

    def get_calendar(self, start_date: date, end_date: date) -> Dict[date, 'Event']:
        """Возвращаем словарь занятий данного типа тренеровок"""
        events = {event.date: event for event in self.event_set.all()}
        # Решение влоб - перебор всех дней с проверкой входят ли они в календарь.
        # TODO: переписать на генератор(yield) - EventClass может возвращать следующий день исходя из настроек
        for n in range(int((end_date - start_date).days)):
            curr_date = start_date + timedelta(n)
            if not (curr_date in events):
                if self.is_event_day(curr_date):
                    events[curr_date] = Event(date=curr_date, event_class=self)

        return events

    # TODO: Нужны методы:
    #   - Создание нового event
    #       +Получение на конкретную дату
    #   - Валидация всех event (а можно ли редактировать описание тренировки, если они уже были?)

    @staticmethod
    def get_absolute_url():
        return reverse_lazy('crm:eventclass_list')

    def __str__(self):
        return self.name


class DayOfTheWeekClass(models.Model):
    """Мероприятие в конкретный день недели, в определенное время, определенной продолжительности"""
    event = models.ForeignKey(EventClass, on_delete=models.CASCADE, verbose_name="Мероприятие")
    # номер дня недели
    day = models.PositiveSmallIntegerField("День недели", validators=[MinValueValidator(0), MaxValueValidator(6)])
    start_time = models.TimeField("Время начала тренировки", default=timezone.now)
    end_time = models.TimeField("Время окнчания тренировки", default=timezone.now)

    class Meta:
        unique_together = ('day', 'event',)


granularity = (
    ('day', 'День'),
    ('week', 'Неделя'),
    ('month', 'Месяц'),
    ('year', 'Год')
)


class SubscriptionsType(models.Model):
    """Типы абонементов
    Описывает продолжительность действия, количество посещений, какие тренировки позволяет посещать"""
    name = models.CharField("Название", max_length=100)
    price = models.FloatField("Стоимость")
    duration_type = models.CharField("Временные рамки абонемента", max_length=20, choices=granularity, default=granularity[0])
    duration = models.PositiveIntegerField("Продолжительность")
    rounding = models.BooleanField("Округление начала действия абонемента", default=False)
    visit_limit = models.PositiveIntegerField("Количество посещений")
    event_class = models.ManyToManyField(EventClass, verbose_name="Допустимые тренировки")

    def __str__(self):
        return 'name: (0)'.format(self.name)

    def get_start_date(self, rounding_date):
        """Возвращает дату начала действия абонемента после округления.
        rounding_date - дата начала действия абонемента до округления"""
        if self.rounding:
            weekday = rounding_date.weekday()
            if self.duration_type == granularity[0][0]:
                start_date = rounding_date
            elif self.duration_type == granularity[1][0]:
                start_date = rounding_date - timedelta(weekday)
            elif self.duration_type == granularity[2][0]:
                start_date = datetime(rounding_date.year, rounding_date.month, 1)
            elif self.duration_type == granularity[3][0]:
                start_date = datetime(rounding_date.year, 1, 1)
        else:
            start_date = rounding_date
        return start_date

    def get_end_date(self, start_date):
        """Возвращает дату окончания действия абонемента.
        start_date - дата начала действия абонемента"""
        end_date = None
        if self.duration_type == granularity[0][0]:
            end_date = start_date + relativedelta(days=self.duration)
        elif self.duration_type == granularity[1][0]:
            end_date = start_date + relativedelta(days=7 * self.duration)
        elif self.duration_type == granularity[2][0]:
            end_date = start_date + relativedelta(months=self.duration)
        elif self.duration_type == granularity[3][0]:
            end_date = start_date + relativedelta(years=self.duration)
        return end_date

    @staticmethod
    def get_absolute_url():
        return reverse('crm:subscriptions')


class Client(models.Model):
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

    def get_absolute_url(self):
        return reverse('crm:client-detail', kwargs={'pk':self.pk})

    @property
    def last_sub(self):
        return self.clientsubscriptions_set.order_by('purchase_date').first

    def __str__(self):
        return self.name


class ClientSubscriptions(models.Model):
    """Абонементы клиента"""
    client = models.ForeignKey(Client,
                               on_delete=models.PROTECT,
                               verbose_name="Ученик")
    subscription = models.ForeignKey(SubscriptionsType,
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

    def extend_duration(self, visits_left_plus):
        self.visits_left += int(visits_left_plus)
        self.end_date = self.end_date + timedelta(self.subscription.duration)
        self.save()

    def get_absolute_url(self):
        return reverse('crm:client-detail', kwargs={'pk': self.client.id})

    def is_expiring(self):
        current_date = datetime.now(timezone.utc)
        end_date = self.end_date
        delta = end_date - current_date
        if (delta.days <= 7 or self.visits_left == 1):
            return True
        else:
            return False

    class Meta:
        ordering = ['purchase_date']


class Event(models.Model):
    """Конкретное мероприятие (тренировка)"""
    date = models.DateField("Дата")
    event_class = models.ForeignKey(EventClass,
                                    on_delete=models.PROTECT,
                                    verbose_name="Тренировка")

    class Meta:
        unique_together = ('event_class', 'date',)

    def clean(self):
        # Проверяем пренадлижит ли указанная дата тренировке
        if not self.event_class.is_event_day(self.date):
            raise ValidationError({"date": "Дата не соответствует тренировке"})

    def __str__(self):
        return self.date.strftime("%Y-%m-%d") + " " + str(self.event_class)
    # TODO: Валидацию по event_class


class Attendance(models.Model):
    """Посещение клиентом мероприятия(тренировки)"""
    client = models.ForeignKey(Client,
                               on_delete=models.PROTECT,
                               verbose_name="Ученик")
    event = models.ForeignKey(Event,
                              on_delete=models.PROTECT,
                              verbose_name="Тренировка")

    class Meta:
        unique_together = ('client', 'event',)

    def __str__(self):
        return self.client.name + " " + str(self.event)
