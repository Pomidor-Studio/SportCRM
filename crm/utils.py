import datetime
import re

import django_filters
from bootstrap_datepicker_plus import DatePickerInput
from django import forms
from django.conf.locale.ru.formats import DATE_INPUT_FORMATS
from django_filters.fields import RangeField
from django_filters.utils import handle_timezone
from django_filters.widgets import SuffixedMultiWidget

VK_PAGE_REGEXP = re.compile('(https?://)?vk.com/(?P<user_id>([A-Za-z0-9_])+)')


class BootstrapRangeWidget(SuffixedMultiWidget):
    template_name = 'django_filters/widgets/multiwidget.html'
    suffixes = ['min', 'max']

    def __init__(self, attrs=None):
        widgets = (
            DatePickerInput(
                format='%d.%m.%Y',
                options={
                    'locale': 'ru',
                }
            ),
            DatePickerInput(
                format='%d.%m.%Y',
                options={
                    'locale': 'ru',
                }
            )
        )
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
            forms.DateField(input_formats=DATE_INPUT_FORMATS,),
            forms.DateField(input_formats=DATE_INPUT_FORMATS,))
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
