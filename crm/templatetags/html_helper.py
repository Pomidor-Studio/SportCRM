from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import TemplateSyntaxError, Node, NodeList
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
                    obj = self.resolve(condition[3], context)
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
