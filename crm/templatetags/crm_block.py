from django import template

from crm.utils import event_color

register = template.Library()


@register.inclusion_tag('tags/subscription_info.html')
def subscription_info(subscription):
    return {'subscription': subscription}


@register.simple_tag(name='event_color')
def event_color_tag(event_class_id: int) -> str:
    return event_color(event_class_id)
