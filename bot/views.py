from __future__ import unicode_literals

import json
from operator import itemgetter

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django_multitenant.utils import set_current_tenant
from rest_framework.generics import UpdateAPIView
from rules.contrib.views import PermissionRequiredMixin

from bot.api.messageHandler import create_answer
from bot.api.messages.base import Message
from bot.models import MessageMeta
from bot.serializers import MessageIgnoranceSerializer
from crm.models import Company

"""
Using VK Callback API version 5.90
For more ditalies visit https://vk.com/dev/callback_api
"""

"""
From Django documentation (https://docs.djangoproject.com/en/1.11/ref/request-response/)
When a page is requested, Django automatically creates an HttpRequest object that contains
metadata about the request. Then Django loads the appropriate view, passing the
HttpRequest as the first argument to the view function.
This argiment is <request> in def index(request):

Decorator <@csrf_exempt> marks a view as being exempt from the protection
ensured by the Django middleware.
For cross site request protection will be used secret key from VK
"""
@csrf_exempt
def gl(request):
    # url: https://mysite.ru/vkbot/

    if request.method == "POST":
        # take POST request from auto-generated variable <request.body>
        # in json format
        data = json.loads(request.body)

        if data['type'] == 'confirmation':
            # VK server request confirmation
            confirmation_token = Company.objects.get(
                vk_group_id=data['group_id']
            ).vk_confirmation_token
            return HttpResponse(
                confirmation_token, content_type="text/plain", status=200)

        if data['type'] == 'message_new':
            # VK server send a message
            company = Company.objects.get(vk_group_id=data['group_id'])
            set_current_tenant(company)
            token = company.vk_access_token

            create_answer(data['object'], token)

    return HttpResponse('ok', content_type="text/plain", status=200)


class IgnoranceList(PermissionRequiredMixin, ListView):
    permission_required = 'message_ignorance'
    template_name = 'bot/message/ignorance.html'
    context_object_name = 'vk_messages'

    def get_queryset(self):
        items = []
        for message_type in Message._registry:
            items.append({
                'uuid': message_type.uuid(),
                'help_text': message_type.detailed_description,
                'is_enabled': message_type.is_enabled_message()
            })
        return sorted(items, key=itemgetter('uuid'))


class ToggleIgnorance(UpdateAPIView):
    lookup_url_kwarg = 'uuid'
    lookup_field = 'uuid'
    serializer_class = MessageIgnoranceSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj, _ = MessageMeta.objects.get_or_create(**filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
