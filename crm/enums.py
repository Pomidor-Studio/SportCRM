from extended_choices import Choices

GRANULARITY = Choices(
    ('DAY', 'day', 'День', {'pluralize': ['день', 'дня', 'дней']}),
    ('WEEK', 'week', 'Неделя', {'pluralize': ['неделя', 'недели', 'недель']}),
    ('MONTH', 'month', 'Месяц', {'pluralize': ['месяц', 'месяца', 'месяцев']}),
    ('YEAR', 'year', 'Год', {'pluralize': ['год', 'года', 'лет']})
)
