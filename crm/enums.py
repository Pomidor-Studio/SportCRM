from extended_choices import Choices

GRANULARITY = Choices(
    ('DAY', 'day', 'День', {'pluralize': ['день', 'дня', 'дней']}),
    ('WEEK', 'week', 'Неделя', {'pluralize': ['неделя', 'недели', 'недель']}),
    ('MONTH', 'month', 'Месяц', {'pluralize': ['месяц', 'месяца', 'месяцев']}),
    ('YEAR', 'year', 'Год', {'pluralize': ['год', 'года', 'лет']})
)

BALANCE_REASON = Choices(
    ('UPDATE_BALANCE', 'Пополнение баланса', 'Пополнение баланса'),
    ('BY_SUBSCRIPTION', 'Покупка абонемента', 'Покупка абонемента'),
    ('ONE_TIME', 'Разовое посещение', 'Разовое посещение'),
    ('ERROR_FIX', 'Исправление ошибки', 'Исправление ошибки'),
    ('OTHER', 'Иное', 'Иное'),
)
