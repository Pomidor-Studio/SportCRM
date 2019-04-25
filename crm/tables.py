import django_tables2 as tables


class ReportTable(tables.Table):
    date = tables.Column(
        verbose_name='Дата',
        orderable=True,
    )
    employee = tables.Column(
        verbose_name='Сотрудник',
    )
    event_class = tables.Column(
        verbose_name='Тренировка',
        orderable=False,
    )
    clients_count = tables.Column(
        verbose_name='Количество учеников',
        orderable=False
    )
    clients_count_one_time = tables.Column(
        verbose_name='По одноразовому абонементу',
        orderable=False
    )
    subs_sales = tables.Column(
        verbose_name='Продано абонементов',
        orderable=False
    )
    profit = tables.Column(
        verbose_name='Собрано денег',
    )

    class Meta:
        template_name = 'django_tables2/bootstrap.html'
        order_by = ('-date',)
