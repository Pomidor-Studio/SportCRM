# Generated by Django 2.1.7 on 2019-04-02 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_squashed_0028_make_visits_non_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptionstype',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Наимеование'),
        ),
        migrations.AlterField(
            model_name='subscriptionstype',
            name='price',
            field=models.FloatField(verbose_name='Цена, ₽'),
        ),
    ]