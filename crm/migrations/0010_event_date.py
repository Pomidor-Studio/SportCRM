# Generated by Django 2.1.5 on 2019-01-20 17:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0009_auto_20190120_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Дата'),
            preserve_default=False,
        ),
    ]
