# Generated by Django 2.1.7 on 2019-04-10 17:51

from django.db import migrations
from django.db.models import F


def remove_one_day(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    ClientSubscriptions = apps.get_model("crm", "ClientSubscriptions")
    ClientSubscriptions.objects.update(end_date=F('end_date') - 1)


def add_one_day(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    ClientSubscriptions = apps.get_model("crm", "ClientSubscriptions")
    ClientSubscriptions.objects.update(end_date=F('end_date') + 1)


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_auto_20190405_1916'),
    ]

    operations = [
        migrations.RunPython(remove_one_day, add_one_day)
    ]
