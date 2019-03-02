from datetime import datetime

from django.urls import reverse
from rest_framework import serializers

from crm.models import Event


class CalendarEventSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    allDay = serializers.BooleanField(default=False)
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_id(self, instance: 'Event'):
        return instance.id if instance.id else id(instance)

    def get_title(self, instance: 'Event'):
        return ''

    def get_start(self, instance: 'Event'):
        weekday = instance.date.weekday()
        start_time = instance.event_class.dayoftheweekclass_set.filter(
            day=weekday
        ).first().start_time

        return datetime.combine(instance.date, start_time)

    def get_end(self, instance: 'Event'):
        weekday = instance.date.weekday()
        end_time = instance.event_class.dayoftheweekclass_set.filter(
            day=weekday
        ).first().end_time
        return datetime.combine(instance.date, end_time)

    def get_url(self, instance: 'Event'):
        return reverse('crm:manager:event-class:event:event-by-date', args=(
            instance.event_class.id,
            instance.date.year,
            instance.date.month,
            instance.date.day
        ))
