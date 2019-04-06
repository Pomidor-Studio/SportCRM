from django import template
from django.utils.safestring import mark_safe

from vk_group_app.utils import signed_clients_display

register = template.Library()


@register.simple_tag
def signed_clients(amount):
    return mark_safe(signed_clients_display(amount))
