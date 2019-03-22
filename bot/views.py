from __future__ import unicode_literals

import json
from operator import itemgetter

from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_multitenant.utils import set_current_tenant
from rest_framework.generics import UpdateAPIView
from rules.contrib.views import PermissionRequiredMixin

from bot.api.messageHandler import create_answer
from bot.api.messages.base import Message
from bot.forms import MessageTemplateEditForm
from bot.models import MessageMeta
from bot.serializers import MessageIgnoranceSerializer
from crm.models import Company
from crm.views.mixin import RedirectWithActionView

from google_tasks.tasks import enqueue

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
            enqueue('create_answer', data['object'], token)

    return HttpResponse('ok', content_type="text/plain", status=200)


class IgnoranceList(PermissionRequiredMixin, ListView):
    permission_required = 'message.ignorance'
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
    queryset = MessageMeta.objects.all()

    def get_message_type(self) -> Message:
        msg_type = next(
            filter(
                lambda msg:
                    msg.uuid() == self.kwargs.get(self.lookup_url_kwarg),
                Message._registry
            ),
            None
        )
        if not msg_type:
            raise Http404()

        return msg_type

    def get_object(self):
        self.msg_type = self.get_message_type()
        try:
            return super().get_object()
        except Http404:
            return MessageMeta.objects.create(
                uuid=self.kwargs.get(self.lookup_url_kwarg),
                template=self.msg_type.default_template
            )


class SingleMessageMixin(SingleObjectMixin):

    def get_message_type(self) -> Message:
        msg_type = next(
            filter(
                lambda msg: msg.uuid() == self.kwargs.get(self.slug_url_kwarg),
                Message._registry
            ),
            None
        )
        if not msg_type:
            raise Http404()

        return msg_type

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Http404:
            return MessageMeta.objects.create(
                uuid=self.kwargs.get(self.slug_url_kwarg),
                template=self.msg_type.default_template
            )


class MessageTemplateEdit(
    PermissionRequiredMixin,
    SingleMessageMixin,
    UpdateView
):
    permission_required = 'message.template'
    form_class = MessageTemplateEditForm
    model = MessageMeta
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    template_name = 'bot/message/template-edit.html'
    msg_type: Message = None

    def get(self, request, *args, **kwargs):
        self.msg_type = self.get_message_type()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'message_caption':
                self.msg_type.detailed_description,
            'message_example':
                self.msg_type.prepare_example_generalized_message(),
            'template_items': self.msg_type.template_args
        })
        return context

    def get_success_url(self):
        return reverse('bot:messages:template-edit', args=(self.object.uuid,))


class ResetMessageTemplate(
    PermissionRequiredMixin,
    SingleMessageMixin,
    RedirectWithActionView
):
    permission_required = 'message.template'
    pattern_name = 'bot:messages:template-edit'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    model = MessageMeta

    def run_action(self):
        msg_type = self.get_message_type()
        obj = self.get_object()
        obj.template = msg_type.default_template
        obj.save()

