# Generated by Django 2.1.7 on 2019-02-26 07:27

from django.db import migrations
import django.db.models.deletion
import django_multitenant.fields


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_safe_delete_models'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={},
        ),
        migrations.AddField(
            model_name='attendance',
            name='subscription',
            field=django_multitenant.fields.TenantForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.PROTECT, to='crm.ClientSubscriptions', verbose_name='Абонемент Клиента'),
        ),
    ]
