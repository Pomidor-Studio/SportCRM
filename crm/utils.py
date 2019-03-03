import datetime

import django_filters
from bootstrap_datepicker_plus import DatePickerInput
from django import forms
from django_filters.fields import RangeField
from django_filters.utils import handle_timezone
from django_filters.widgets import SuffixedMultiWidget


class BootstrapRangeWidget(SuffixedMultiWidget):
    template_name = 'django_filters/widgets/multiwidget.html'
    suffixes = ['min', 'max']

    def __init__(self, attrs=None):
        widgets = (DatePickerInput(format='%d.%m.%Y'), DatePickerInput(format='%d.%m.%Y'))
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class BootstrapDateRangeWidget(BootstrapRangeWidget):
    suffixes = ['after', 'before']


class BootstrapDateRangeField(RangeField):
    widget = BootstrapDateRangeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.DateField())
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            start_date, stop_date = data_list
            if start_date:
                start_date = handle_timezone(
                    datetime.datetime.combine(start_date, datetime.time.min),
                    False
                )
            if stop_date:
                stop_date = handle_timezone(
                    datetime.datetime.combine(stop_date, datetime.time.max),
                    False
                )
            return slice(start_date, stop_date)
        return None


class BootstrapDateFromToRangeFilter(django_filters.RangeFilter):
    field_class = BootstrapDateRangeField

    
def pluralize(singular, plural1, plural2, count):
    if count % 10 == 1 and count % 100 != 11:
        return singular
    elif 2 <= count % 10 <= 4 and (count % 100 < 12 or count % 100 > 14):
        return plural1
    elif count % 10 == 0 or (5 <= count % 10 <= 9) or (11 <= count % 100 <= 14):
        return plural2

    return singular
