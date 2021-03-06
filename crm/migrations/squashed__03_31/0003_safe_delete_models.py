# Generated by Django 2.1.7 on 2019-02-20 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_add_coach_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='coach',
            name='deleted',
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='deleted',
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='subscriptionstype',
            name='deleted',
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='coach',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='location',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='subscriptionstype',
            unique_together=set(),
        ),
    ]
