# Generated by Django 2.1.7 on 2019-03-25 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0027_fill_visits_on_by_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientsubscriptions',
            name='visits_on_by_time',
            field=models.PositiveSmallIntegerField(verbose_name='Количество визитов на момент покупки'),
        ),
    ]