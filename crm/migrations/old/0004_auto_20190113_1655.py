# Generated by Django 2.1.5 on 2019-01-13 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_auto_20190112_0020'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crm.Client')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crm.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Coach',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.CharField(blank=True, max_length=1000)),
            ],
        ),
        migrations.AddField(
            model_name='eventclass',
            name='coach',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='crm.Coach'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventclass',
            name='location',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='crm.Location'),
            preserve_default=False,
        ),
    ]