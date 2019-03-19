from __future__ import annotations

from datetime import datetime

from django.urls import reverse
from rest_framework import serializers

from crm.models import Event, ClientSubscriptions


class CalendarEventSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    allDay = serializers.BooleanField(default=False)
    start = serializers.SerializerMethodField()
    end = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()

    event_colors = [
        '#007bff',
        '#6610f2',
        '#6f42c1',
        '#e83e8c',
        '#dc3545',
        '#fd7e14',
        '#ffc107',
        '#28a745',
        '#20c997',
        '#17a2b8',
        '#6c757d',
        '#343a40',
        '#007bff',
        '#6c757d',
        '#28a745',
        '#17a2b8',
        '#ffc107',
        '#343a40',
        '#026670',
    ]
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
