from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    subscription_name = models.CharField(max_length=100)
    price = models.IntegerField()
    duration = models.IntegerField()
    visit_limit = models.IntegerField()


class Client(models.Model):
    client_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255,
                               blank=True)
    birthday = models.DateField(null=True)
    phone_number = models.CharField(max_length=50,
                                    blank=True)
    email_address = models.CharField(max_length=50,
                                     blank=True)


class ClientSubscriptions(models.Model):
    client_id = models.ForeignKey(Client,
                                  on_delete=models.CASCADE)
    subscription_id = models.ForeignKey(Subscription,
                                        on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
