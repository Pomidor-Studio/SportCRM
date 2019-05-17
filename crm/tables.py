import django_tables2 as tables
from django.urls import reverse

from crm.models import Event


def event_class_link(value, record):
    url = reverse('crm:manager:event:visit-report')
    link = '{url}?year={year}&month={month}&event_class={event_class}'
    return link.format(
        url=url,
        title=value.name,
        year=record.date.year,
        month=record.date.month,
        event_class=record.event_class.id,
    )


class EventReportTable(tables.Table):
    coach = tables.Column(accessor='event_class.coach.user',  verbose_name='Тренер')
    event_class = tables.Column(
        verbose_name='Тренировка',
        linkify=event_class_link
    )
    clients_count = tables.Column(
        accessor='get_present_clients_count',
        verbose_name='Количество учеников',
        orderable=False
    )
    clients_count_one_time = tables.Column(
        accessor='get_clients_count_one_time_sub',
        verbose_name='По одноразовому абонементу',
        orderable=False
    )
    subs_sales = tables.Column(
        accessor='get_subs_sales',
        verbose_name='Продано абонементов',
        orderable=False
    )
    profit = tables.Column(
        accessor='get_profit',
        verbose_name='Собрано денег',
        orderable=False
    )

    # def link_render(self, record, value):
    #     return self.text_value(record, value)
    # def render_event_class(self, value):
    #     url = reverse()
    #     link = '<a href="{url}?year={year}&month={month}&event_class={event_class}">{title}</a>'
    #     return link.format(
    #         url=url,
    #         title=value.name,
    #         year=value.date.year,
    #         month=value.date.month,
    #         event_class=value.event_class.id,
    #     )

    class Meta:
        model = Event
        template_name = 'django_tables2/bootstrap.html'
        fields = ('date',)
        order_by = ('-date',)


