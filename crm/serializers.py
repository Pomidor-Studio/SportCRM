from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.conf.locale.ru.formats import DATE_INPUT_FORMATS
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from django.urls import reverse
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from crm.enums import GRANULARITY
from crm.events import next_day
from crm.models import (
    Event, ClientSubscriptions, SubscriptionsType, Manager,
    User,
    EventClass,
    EventClassSection,
)


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


class RegisterCompanySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    phone = PhoneNumberField(required=True)
    email = serializers.EmailField(required=True)
    agree_oferta = serializers.BooleanField(required=True)

    def create(self, validated_data):
        password = get_user_model().objects.make_random_password()
        manager = Manager.objects.create_with_company(
            company_name=validated_data['name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            password=password
        )
        from gcp.tasks import enqueue
        enqueue('send_registration_notification', manager.user_id, password)
        enqueue('send_registration_notification_manager', manager.user_id)
        return manager

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if get_user_model().objects.filter(email=attrs['email']).exists():
            raise ValidationError(
                'Заявка с такой почтой уже была отправлена!',
                code='email-error'
            )
        if Manager.objects.filter(phone_number=attrs['phone']).exists():
            raise ValidationError(
                'Заявка с таким телефонм уже была отправленна!',
                code='email-error'
            )
        return attrs

    def to_representation(self, instance):
        return {'success': True}


class EventClassDaySerializer(serializers.Serializer):
    # ISO weekday format, not zero based
    day_num = serializers.IntegerField(min_value=1, max_value=7)
    from_time = serializers.TimeField(format='%H:%M')
    to_time = serializers.TimeField(format='%H:%M')

    def create(self, validated_data):
        return object()


class EventClassSectionSerializer(serializers.Serializer):
    section_id = serializers.IntegerField(allow_null=True)
    singular_event = serializers.BooleanField(default=True)
    from_date = serializers.DateField()
    to_date = serializers.DateField(allow_null=True)
    day_data = EventClassDaySerializer(many=True)

    def create(self, validated_data):
        return object()


class EventClassEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventClass
        fields = (
            'name', 'location', 'coach', 'new', 'updated', 'deleted',
            'oneTimePrice', 'planedAttendance'
        )

    new = EventClassSectionSerializer(
        allow_null=True, many=True, required=False)
    updated = EventClassSectionSerializer(
        allow_null=True, many=True, required=False)
    deleted = EventClassSectionSerializer(
        allow_null=True, many=True, required=False)
    oneTimePrice = serializers.FloatField(allow_null=True)
    planedAttendance = serializers.IntegerField(allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if (attrs['new'] is None or not len(attrs['new'])) and \
                (attrs['updated'] is None or not len(attrs['updated'])) and \
                (attrs['deleted'] is None or not len(attrs['deleted'])):
            raise serializers.ValidationError(
                'Not data provided', code='no-data')
        return attrs

    def create_events(
        self,
        period: EventClassSectionSerializer,
        event_class: EventClass
    ):
        days = {
            x['day_num']: (
                x['from_time'], x['to_time']
            ) for x in period['day_data']
        }
        section = EventClassSection.objects.create(
            event_class=event_class, singular_event=period['singular_event'],
            from_date=period['from_date'], to_date=period['to_date'],
            day_data=days
        )

        if period['singular_event']:
            self._create_singular(section)
        else:
            self._create_many(section)

    def _delete_event(self, event: Event):
        for marked_att in event.attendance_set.filter(marked=True):
            marked_att.subscription.visits_left += 1
            marked_att.subscription.save()

        event.attendance_set.all().delete()
        event.delete()

    def _delete_singular(self, section):
        if section.from_date > datetime.today().date():
            events = Event.objects.filter(
                event_class__in=list(
                    EventClass.objects
                    .filter(eventclasssection=section)
                    .values_list('id', flat=True)
                ),
                date=section.from_date
            )
            for event in events:
                self._delete_event(event)

            section.delete()

    def _delete_many(self, section, possible_weekdays=None):
        weekdays = sorted(possible_weekdays or section.day_data.keys())
        # Convert from iso to python zero based weekday
        weekdays = [int(x) - 1 for x in weekdays]
        for day in next_day(section.from_date, section.to_date, weekdays):
            if day > datetime.today().date():
                events = Event.objects.filter(
                    event_class__in=list(
                        EventClass.objects
                        .filter(eventclasssection=section)
                        .values_list('id', flat=True)
                    ),
                    date=day
                )
                for event in events:
                    self._delete_event(event)

        if possible_weekdays is None:
            section.delete()

    def delete_events(
        self,
        period: EventClassSectionSerializer
    ):
        try:
            section = EventClassSection.objects.get(id=period['section_id'])
        except EventClassSection.DoesNotExist:
            return
        if section.singular_event:
            self._delete_singular(section)
        else:
            self._delete_many(section)

    def _create_singular(
        self,
        section: EventClassSection
    ):
        if section.from_date > datetime.today().date():
            Event.objects.create(
                event_class=section.event_class, event_class_section=section,
                date=section.from_date
            )

    def _create_many(self, section: EventClassSection, possible_weekdays=None):
        weekdays = sorted(possible_weekdays or section.day_data.keys())
        # Convert from iso to python zero based weekday
        weekdays = [int(x) - 1 for x in weekdays]
        for day in next_day(section.from_date, section.to_date, weekdays):
            if day > datetime.today().date():
                Event.objects.create(
                    event_class=section.event_class,
                    event_class_section=section,
                    date=day
                )

    def update_events(
        self,
        period: EventClassSectionSerializer
    ):
        days = {
            x['day_num']: (
                x['from_time'], x['to_time']
            ) for x in period['day_data']
        }
        try:
            section = EventClassSection.objects.get(id=period['section_id'])
        except EventClassSection.DoesNotExist:
            return

        if section.singular_event:
            if section.from_date != period['from_date']:
                self._delete_singular(section)
                self._create_singular(section)
        else:
            new_days = set(days.keys())
            old_days = set(section.day_data.keys())
            if old_days - new_days:
                self._delete_many(
                    section, [int(x) for x in (old_days - new_days)])
            if new_days - old_days:
                self._create_many(
                    section, [int(x) for x in (new_days - old_days)]
                )

        section.day_data = days
        section.save()

    def modifyOneTimePrice(
        self, event_class: EventClass, price: Optional[float]
    ):
        try:
            one_time_sub = SubscriptionsType.all_objects.get(
                one_time=True, event_class=event_class)
            if price and price > 0:
                if one_time_sub.deleted:
                    one_time_sub.undelete()
                one_time_sub.price = price
                one_time_sub.save()
            else:
                one_time_sub.delete()
        except SubscriptionsType.DoesNotExist:
            if price and price > 0:
                sub = SubscriptionsType(
                    name='Разовое посещение ' + event_class.name,
                    price=price,
                    duration_type=GRANULARITY.DAY,
                    duration=1,
                    rounding=False,
                    visit_limit=1,
                    one_time=True
                )
                sub.save()
                sub.event_class.add(event_class)

    def modify_events(self, event_class, validated_data):
        for new_period in validated_data['new']:
            self.create_events(new_period, event_class)

        for update_period in validated_data['updated']:
            self.update_events(update_period)

        for delete_period in validated_data['deleted']:
            self.delete_events(delete_period)

        self.modifyOneTimePrice(
            event_class, validated_data['oneTimePrice'])

    def create(self, validated_data):
        with transaction.atomic():
            event_class = EventClass.objects.create(
                name=validated_data['name'],
                location=validated_data['location'],
                coach=validated_data['coach']
            )

            self.modify_events(event_class, validated_data)

        return event_class

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.name = validated_data['name']
            instance.location = validated_data['location']
            instance.coach = validated_data['coach']

            instance.save()

            self.modify_events(instance, validated_data)

        return instance

    def to_representation(self, instance):
        return {
            'id': instance.id
        }
