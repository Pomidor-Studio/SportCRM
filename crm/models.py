from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Location(models.Model):
    name = models.CharField("Название",
                            max_length=100)
    address = models.CharField("Адрес",
                               max_length=1000,
                               blank=True)

    def __str__(self):
        return self.name


class Coach(models.Model):
    name = models.CharField("Имя",
                            max_length=100)

    def __str__(self):
        return self.name


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

    def is_event_day(self, day: datetime) -> bool:
        """Входит ли переданный день в мероприятия (есть ли в этот день тренировка) """
        # TODO: тут надо написать логику по определению входит ли дата в мероприятие
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

    # TODO: Нужны методы:
    #   - Создание нового event
    #   - Получение списка event-ов по диапазону дат (как сохраненных, так и гипотетических).
    #       +Получение на конкретную дату
    #   - Валидация всех event (а можно ли редактировать описание тренировки, если они уже были?)
    #


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
    start_time = models.TimeField("Время начала тренировки")
    duration = models.IntegerField("Продолжительность (мин.)", default=60)

    class Meta:
        unique_together = ('day', 'event',)


granularity = (
    ('day', 'День'),
    ('week', 'Неделя'),
    ('month', 'Месяц'),
    ('year', 'Год'),
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
        return 'name: (0), initial: (1)'.format(self.name, self.initial)

    def rounding_to_weekday(rounding_date):
        weekday = rounding_date.weekday()
        monday = rounding_date - datetime.timedelta(weekday)
        return monday.strftime("%Y-%m-%d 00:00:00")

    def rounding_to_month(rounding_date):
        month = datetime.datetime(rounding_date.year, rounding_date.month, 1)
        return month.strftime("%Y-%m-%d 00:00:00")

    def rounding_to_year(rounding_date):
        year = datetime.datetime(rounding_date.year, 1, 1)
        return year.strftime("%Y-%m-%d 00:00:00")

    def get_end_date(self, rounding_date):
        end_date = None
        weekday = rounding_date.weekday()
        if self.duration_type == 'day':
            end_date = rounding_date
        elif self.duration_type == 'week':
            end_date = rounding_date + datetime.timedelta(7 - weekday)
        elif self.duration_type == 'month':
            end_date = datetime.datetime(rounding_date.year, rounding_date.month + 1, 1)
        elif self.duration_type == 'year':
            end_date = datetime.datetime(rounding_date.year + 1, 1, 1)
        return end_date

    def get_absolute_url(self):
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
    purchase_date = models.DateTimeField("Дата покупки",
                                         default=timezone.now)
    start_date = models.DateTimeField("Дата начала",
                                      default=timezone.now)
    end_date = models.DateTimeField(null=True)
    price = models.FloatField("Стоимость")
    visits_left = models.PositiveIntegerField("Остаток посещений")

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(self.subscription.duration)
        super(ClientSubscriptions, self).save(*args, **kwargs)

    def extend_duration(self, visits_left_plus):
        self.visits_left += int(visits_left_plus)
        self.end_date = self.end_date + timedelta(self.subscription.duration)
        self.save()

    def get_absolute_url(self):
        return reverse('crm:client-detail', kwargs={'pk': self.client.id})

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
