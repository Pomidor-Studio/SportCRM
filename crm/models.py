from datetime import datetime
from django.db import models
from django.utils import timezone
from django.urls import reverse_lazy, reverse


class SubscriptionsType(models.Model):
    """Типы абонементов"""
    name = models.CharField(max_length=100)
    price = models.FloatField()
    duration = models.PositiveIntegerField()
    visit_limit = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('crm:subscriptions')

class Client(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255,
                               blank=True)
    birthday = models.DateField(null=True)
    phone_number = models.CharField(max_length=50,
                                    blank=True)
    email_address = models.CharField(max_length=50,
                                     blank=True)

    def get_absolute_url(self):
        return reverse('crm:clients')

    @property
    def last_sub(self):
        return self.clientsubscriptions_set.order_by('purchase_date').first

class ClientSubscriptions(models.Model):
    """Абонементы клиента"""
    client = models.ForeignKey(Client,
                               on_delete=models.PROTECT)
    subscription = models.ForeignKey(SubscriptionsType,
                                     on_delete=models.PROTECT)
    purchase_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self):
        return reverse('crm:client-detail', kwargs={'pk': self.client.id})

    class Meta:
        ordering = ['purchase_date']


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=1000,
                               blank=True)

    def __str__(self):
        return self.name


class Coach(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class EventClass(models.Model):
    """Описание мероприятия (Класс вид). Например, тренировки по средам и пятницам у новичков"""
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location,
                                 on_delete=models.PROTECT)
    coach = models.ForeignKey(Coach,
                              on_delete=models.PROTECT)

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


class Event(models.Model):
    """Конкретное мероприятие (тренировка)"""
    event_date = models.DateField
    event_class = models.ForeignKey(EventClass,
                                    on_delete=models.PROTECT)
    # TODO: Валидацию по event_class


class Attendance(models.Model):
    """Посещение клиентом мероприятия(тренировки)"""
    client = models.ForeignKey(Client,
                               on_delete=models.PROTECT)
    event = models.ForeignKey(Event,
                              on_delete=models.PROTECT)
