from bootstrap4.components import render_alert
from django import template
from django.contrib.messages.storage.base import Message
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html

register = template.Library()

# Port of https://github.com/noirbizarre/django.js/blob/master/djangojs/templatetags/js.py  # noqa


@register.simple_tag
def javascript(filename, type='text/javascript'):
    """A simple shortcut to render a
    ``script`` tag to a static javascript file"""

    if '?' in filename and len(filename.split('?')) is 2:
        filename, params = filename.split('?')
        params = '?' + params
    else:
        params = ''
    return format_html(
        '<script type="{}" src="{}{}"></script>',
        type, staticfiles_storage.url(filename), params
    )


@register.simple_tag
def js(filename, type='text/javascript'):
    """"A simple shortcut to render a
    ``script`` tag to a static javascript file"""
    return javascript(filename, type=type)


@register.simple_tag
def css(filename):
    """A simple shortcut to render a ``link`` tag to a static CSS file'"""
    return format_html(
        '<link rel="stylesheet" type="text/css" href="{}" />',
        staticfiles_storage.url(filename)
    )


DJANGO_TO_BOOTSTRAP = {
    'debug': 'dark',
    'info': 'info',
    'success': 'success',
    'warning': 'warning',
    'error': 'danger'
}


@register.simple_tag
def bootstrap_alert_message(message: Message, dismissable=True):
    return render_alert(
        str(message), DJANGO_TO_BOOTSTRAP[message.level_tag], dismissable)
