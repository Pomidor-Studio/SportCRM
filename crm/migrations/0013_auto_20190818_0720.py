# Generated by Django 2.1.7 on 2019-08-18 07:20

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0012_auto_20190718_0243'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventclass',
            name='planned_attendance',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Плановая посещаемость'),
        ),
    ]
