# Generated by Django 2.1.5 on 2019-01-11 19:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_auto_20190111_2209'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='EventClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionsType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('price', models.IntegerField()),
                ('duration', models.IntegerField()),
                ('visit_limit', models.IntegerField()),
            ],
        ),
        migrations.RenameField(
            model_name='client',
            old_name='client_name',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='clientsubscriptions',
            name='client_id',
        ),
        migrations.RemoveField(
            model_name='clientsubscriptions',
            name='subscription_id',
        ),
        migrations.AddField(
            model_name='clientsubscriptions',
            name='client',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='crm.Client'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Subscription',
        ),
        migrations.AddField(
            model_name='event',
            name='event_class',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crm.EventClass'),
        ),
        migrations.AddField(
            model_name='clientsubscriptions',
            name='subscription',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='crm.SubscriptionsType'),
            preserve_default=False,
        ),
    ]
