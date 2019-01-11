from django.db import models
from django.utils import timezone


class subscriptions(models.Model):
    id = models.AutoField(primary_key=True)
    subscription_name = models.CharField(max_length=100)
    price = models.IntegerField()
    duration = models.IntegerField()
    visit_limit = models.IntegerField()


class clients(models.Model):
    id = models.AutoField(primary_key=True)
    client_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    birthdate = models.DateField()
    phone_number = models.CharField(max_length=50, default=None, null=True)
    email_adress = models.CharField(max_length=50, default=None, null=True)


class client_subscriptions(models.Model):
    id = models.AutoField(primary_key=True)
    client_id = models.ForeignKey(clients, on_delete=models.CASCADE)
    subscription_id = models.ForeignKey(
        subscriptions, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
