# Generated by Django 2.1.7 on 2019-03-23 19:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0024_merge_20190322_2306'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientbalancechangehistory',
            name='actual_entry_date',
        ),
    ]
