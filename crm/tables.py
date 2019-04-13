import django_tables2 as tables

from crm.models import Event


class EventReportTable(tables.Table):
    coach = tables.Column(accessor='event_class.coach')
    event_class = tables.Column(
        accessor='event_class.name',
        verbose_name='Класс мероприятия'
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

    class Meta:
        model = Event
        template_name = 'django_tables2/bootstrap.html'
        fields = ('date',)
