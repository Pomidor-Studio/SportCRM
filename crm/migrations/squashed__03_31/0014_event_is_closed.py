# Generated by Django 2.1.7 on 2019-03-09 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0013_merge_20190308_2318'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_closed',
            field=models.BooleanField(default=False, verbose_name='Тренировка закрыта'),
        ),
    ]
