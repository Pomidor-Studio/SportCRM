# Generated by Django 2.1.5 on 2019-01-27 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0015_merge_20190127_1600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventclass',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Название'),
        ),
    ]