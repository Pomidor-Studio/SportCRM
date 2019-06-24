from django import template

register = template.Library()


@register.inclusion_tag('tags/subscription_info.html')
def subscription_info(subscription):
    return {'subscription': subscription}
