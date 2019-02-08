from datetime import datetime
from datetime import timedelta
from calendar import monthrange
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
        duration_in_days = self.subscribe_duration_in_days(start_date)
        end_date = start_date + timedelta(duration_in_days)
        return end_date

    def subscribe_duration_in_days(self, start_date):
        duration_in_days = 0
        if self.duration_type == granularity[0][0]:
            duration_in_days = 1 * self.duration
        elif self.duration_type == granularity[1][0]:
            duration_in_days = 7 * self.duration
        elif self.duration_type == granularity[2][0]:
            duration_in_days = self.month_or_year(start_date, granularity[2])
        elif self.duration_type == granularity[3][0]:
            duration_in_days = self.month_or_year(start_date, granularity[3])
        return duration_in_days

    def month_or_year(self, start_date, m_or_y):
        i = 0
        duration_in_days = 0
        factor = 1
        if m_or_y == granularity[3]:
            factor = 12
        while i < self.duration * factor:
            days_in_month = monthrange(start_date.year, start_date.month)[1]
            duration_in_days = duration_in_days + days_in_month
            start_date = start_date + timedelta(days_in_month)
            i = i + 1
        return duration_in_days

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
