from django.db import models
from django.utils import timezone


class SubscriptionsType(models.Model):
    """Типы абонементов"""
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    duration = models.IntegerField()
    visit_limit = models.IntegerField()


class Client(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255,
                               blank=True)
    birthday = models.DateField(null=True)
    phone_number = models.CharField(max_length=50,
                                    blank=True)
    email_address = models.CharField(max_length=50,
                                     blank=True)


class ClientSubscriptions(models.Model):
    """Абонементы клиента"""
    client = models.ForeignKey(Client,
                               on_delete=models.PROTECT)
    subscription = models.ForeignKey(SubscriptionsType,
                                     on_delete=models.PROTECT)
    purchase_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)


class EventClass(models.Model):
    """Описание мероприятия (Класс вид). Например, тренировки по средам и пятницам у новичков"""
    name = models.CharField(max_length=100)


class Event(models.Model):
    """Конкретное мероприятие (тренировка)"""
    event_date = models.DateField
    event_class = models.ForeignKey(EventClass,
                                    on_delete=models.PROTECT)


