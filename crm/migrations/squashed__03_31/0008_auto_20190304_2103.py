# Generated by Django 2.1.7 on 2019-03-04 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0007_add_canceled_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='vk_access_token',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='Токен группы вк'),
        ),
        migrations.AddField(
            model_name='company',
            name='vk_confirmation_token',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Строка-подтверждение'),
        ),
        migrations.AddField(
            model_name='company',
            name='vk_group_id',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='ИД группы вк'),
        ),
    ]
