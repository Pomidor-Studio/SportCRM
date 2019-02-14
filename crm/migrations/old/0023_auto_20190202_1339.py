# Generated by Django 2.1.5 on 2019-02-02 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0022_auto_20190130_0339'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionstype',
            name='duration_type',
            field=models.CharField(choices=[('day', 'День'), ('week', 'Неделя'), ('month', 'Месяц'), ('year', 'Год')], default=('day', 'День'), max_length=20, verbose_name='Временные рамки абонемента'),
        ),
        migrations.AddField(
            model_name='subscriptionstype',
            name='rounding',
            field=models.BooleanField(default=False, verbose_name='Округление начала действия абонемента'),
        ),
        migrations.AlterField(
            model_name='subscriptionstype',
            name='duration',
            field=models.PositiveIntegerField(verbose_name='Продолжительность'),
        ),
    ]