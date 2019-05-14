from datetime import datetime, date

import vk
from bootstrap4.components import render_alert
from bootstrap4.forms import render_label
from bootstrap4.renderers import FieldRenderer
from bootstrap4.text import text_value
from bootstrap4.utils import render_tag
from django import template
from django.conf import settings
from django.contrib.messages.storage.base import Message
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.cache import cache
from django.template import Node, NodeList, TemplateSyntaxError
from django.utils.html import format_html, escape, strip_tags
from django.utils.safestring import mark_safe
from transliterate.utils import _

from contrib import text_utils

from crm.auth.one_time_login import get_one_time_login_link

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
def vk_small_avatar(vk_user_id):
    cache_key = f'vk_photo_50_{vk_user_id}'
    photo = cache.get(cache_key, None)
    if photo:
        return photo

    session = vk.Session()
    api = vk.API(session, v=5.90)

    try:
        photo = api.users.get(
            access_token=settings.VK_GROUP_TOKEN,
            user_ids=str(vk_user_id),
            fields='photo_50'
        )[0]['photo_50']
    except (IndexError, KeyError):
        photo = ''

    cache.set(cache_key, photo, timeout=86400)  # Keep in cache one day

    return photo


def get_vk_user_ids(vk_user_domains):
    session = vk.Session()
    api = vk.API(session, v=5.90)
    vk_user_ids = [None] * len(vk_user_domains)
    domains = ",".join(vk_user_domains)

    results = api.users.get(
        access_token=settings.VK_GROUP_TOKEN,
        user_ids=domains,
        fields='domain, screen_name'
    )

    for result in results:
        user_id = 'id' + str(result['id'])
        screen_name = result['screen_name']
        for i, domain in enumerate(vk_user_domains):
            if domain == user_id or domain == screen_name:
                vk_user_ids[i] = result['id']

    return vk_user_ids


allowed_date_formats_ru = 'ГГГГ-ММ-ДД, ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ'


def try_parse_date(text):
    if isinstance(text, date):
        return text
    if isinstance(text, datetime):
        return text.date()

    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('Неверный формат даты')


@register.simple_tag
def bootstrap_alert_message(message: Message, dismissable=True):
    return render_alert(
        str(message), DJANGO_TO_BOOTSTRAP[message.level_tag], dismissable)


class DayOfWeekRenderer(FieldRenderer):

    def post_widget_render(self, html):
        return html + render_tag(
            'div', {'class': 'form-check-input-div'}
        ) + render_label(
            content=self.field.label,
            label_for=self.field.id_for_label,
            label_title=escape(strip_tags(self.field_help)),
            label_class="form-check-label",
        )


@register.simple_tag
def bootstrap_dayofweek_render(field):
    return DayOfWeekRenderer(field).render()

  
class IfHasPermNode(Node):

    def __init__(self, conditions_nodelists):
        self.conditions_nodelists = conditions_nodelists

    def __repr__(self):
        return '<%s>' % self.__class__.__name__

    def __iter__(self):
        for _, nodelist in self.conditions_nodelists:
            yield from nodelist

    @property
    def nodelist(self):
        return NodeList(self)

    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    def render(self, context):
        for condition, nodelist in self.conditions_nodelists:

            if condition is not None:           # if / elif clause
                perm = self.resolve(condition[0], context)
                user = self.resolve(condition[1], context)
                try:
                    obj = self.resolve(condition[2], context)
                except IndexError:
                    obj = None

                if not hasattr(user, 'has_perm'):
                    # swapped user model that doesn't support permissions
                    match = False
                else:
                    match = user.has_perm(perm, obj)
            else:                               # else clause
                match = True

            if match:
                return nodelist.render(context)

        return ''


@register.tag('ifhasperm')
def if_has_perm(parser, token):
    # {% if ... %}
    bits = token.split_contents()[1:]

    if not 2 <= len(bits) <= 3:
        raise template.TemplateSyntaxError(
            "'ifhasperm' tag takes two or three arguments"
        )

    nodelist = parser.parse(('else', 'endifhasperm'))
    conditions_nodelists = [(bits, nodelist)]
    token = parser.next_token()

    # {% else %} (optional)
    if token.contents == 'else':
        nodelist = parser.parse(('endifhasperm',))
        conditions_nodelists.append((None, nodelist))
        token = parser.next_token()

    # {% endif %}
    if token.contents != 'endifhasperm':
        raise TemplateSyntaxError(
            'Malformed template tag at line {0}: "{1}"'.format(token.lineno,
                                                               token.contents))

    return IfHasPermNode(conditions_nodelists)


def render_alert(content, alert_type=None, dismissable=True):
    """
    Render a Bootstrap alert
    Port from bootstrap4, as it is bit buggy, and don't allow mark_safe
    """
    button = ""
    if not alert_type:
        alert_type = "info"
    css_classes = ["alert", "alert-" + text_value(alert_type)]
    if dismissable:
        css_classes.append("alert-dismissable")
        button = (
            '<button type="button" class="close" '
            + 'data-dismiss="alert" aria-label="{}">&times;</button>'
        )
        button = button.format(_("close"))
    button_placeholder = mark_safe("__BUTTON__")
    return mark_safe(
        render_tag(
            "div",
            attrs={"class": " ".join(css_classes), "role": "alert"},
            content=button_placeholder + text_value(content),
        ).replace(button_placeholder, button)
    )


@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def pluralize(amount, singular, plural1, plural2):
    return text_utils.pluralize(singular, plural1, plural2, amount)


@register.simple_tag(takes_context=True)
def one_time_login_link(context, user):
    return get_one_time_login_link(context.request.get_host(), user)
