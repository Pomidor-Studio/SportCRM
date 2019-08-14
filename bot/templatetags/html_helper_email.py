from crm import views
from crm.auth.one_time_login import get_one_time_login_link
from django import template
from django.conf import settings
register = template.Library()

@register.simple_tag
def one_time_login_link(user):
    return get_one_time_login_link(settings.HOST, user)


@register.simple_tag
def host():
    return settings.HOST
