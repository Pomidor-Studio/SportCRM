# Generated by Django 2.1.5 on 2019-01-24 14:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0012_auto_20190124_1932'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='date_from',
        ),
        migrations.RemoveField(
            model_name='event',
            name='date_to',
        ),
        migrations.AddField(
            model_name='event',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Дата'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventclass',
            name='date_from',
            field=models.DateField(blank=True, null=True, verbose_name='Дата с'),
        ),
        migrations.AddField(
            model_name='eventclass',
            name='date_to',
            field=models.DateField(blank=True, null=True, verbose_name='Дата по'),
        ),
    ]