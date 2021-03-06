from __future__ import annotations

from datetime import datetime
from django.conf.locale.ru.formats import DATE_INPUT_FORMATS

from django.urls import reverse
from rest_framework import serializers

from crm.models import Event, ClientSubscriptions, SubscriptionsType


class CalendarEventSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    allDay = serializers.BooleanField(default=False)
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()

    event_colors = [
        '#D9F3FB',
        '#ECE5CB',
        '#EADCF5',
        '#CBFFEC',
        '#FFE9F2',
        '#FFCACA',
        '#FFE5D2',
        '#FFF5C0',
        '#D6F2B6'
    ]
    canceled_event_color = '#DDDDDD'
    event_colors_len = len(event_colors)

    def get_id(self, instance: Event):
        return instance.id if instance.id else id(instance)

    def get_title(self, instance: Event):
        return instance.event_class_name

    def get_start(self, instance: Event):
        return datetime.combine(instance.date, instance.start_time)

    def get_end(self, instance: Event):
        return datetime.combine(instance.date, instance.end_time)

    def get_url(self, instance: Event):
        return reverse('crm:manager:event-class:event:event-by-date', args=(
            instance.event_class.id,
            instance.date.year,
            instance.date.month,
            instance.date.day
        ))

    def get_color(self, instance: Event):
        if instance.is_canceled:
            return self.canceled_event_color
        return self.event_colors[
            instance.event_class_id % self.event_colors_len
        ]


class ClientSubscriptionCheckOverlappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientSubscriptions
        fields = [
            'is_overlapping',
            'is_overlapping_with_cancelled',
            'canceled_events_count'
        ]


class SubscriptionRangeSerializer(serializers.Serializer):
    requested_date = serializers.DateField(
        write_only=True,
        input_formats=DATE_INPUT_FORMATS
    )
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    def get_start_date(self, instance: SubscriptionsType):
        return (
            instance
            .start_date(self.context['requested_date'])
            .strftime('%d.%m.%Y')
        )

    def get_end_date(self, instance: SubscriptionsType):
        return (
            instance
            .end_date(self.context['requested_date'])
            .strftime('%d.%m.%Y')
        )
