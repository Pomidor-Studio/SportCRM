from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.urls import reverse_lazy, reverse


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
    name = models.CharField("Назвение",
                            max_length=100)
    location = models.ForeignKey(Location,
                                 on_delete=models.PROTECT,
                                 verbose_name="Расположение")
    coach = models.ForeignKey(Coach,
                              on_delete=models.PROTECT,
                              verbose_name="Тренер"
                              )

    def is_event_day(self, day: datetime) -> bool:
        """Входит ли переданный день в мероприятия (есть ли в этот день тренировка) """
        # TODO: тут надо написать логику по определению входит ли дата в мероприятие
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


class SubscriptionsType(models.Model):
    """Типы абонементов
    Описывает продолжительность действия, количество посещений, какие тренировки позволяет посещать"""
    name = models.CharField("Название",
                            max_length=100)
    price = models.FloatField("Стоимость")
    duration = models.PositiveIntegerField("Продолжительность (дни)")
    visit_limit = models.PositiveIntegerField("Количество посещений")
    event_class = models.ManyToManyField(EventClass,
                                         verbose_name="Допустимые тренировки")

    def __str__(self):
        return self.name

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

    def get_absolute_url(self):
        return reverse('crm:clients')

    @property
    def last_sub(self):
        return self.clientsubscriptions_set.order_by('purchase_date').first


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
    # TODO: Исследовать целесообразность отнаследовать клиентские абонементы от абонементов (или выделить общую часть)
    price = models.FloatField("Стоимость")
    visits_left = models.PositiveIntegerField("Ост0аток посещений")

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
