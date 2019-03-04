# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from bot.api.messageHandler import create_answer
from crm.models import Company

import json

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
@csrf_exempt #exempt index() function from built-in Django protection
def gl(request): #url: https://mysite.ru/vkbot/

    if (request.method == "POST"):
        data = json.loads(request.body)# take POST request from auto-generated variable <request.body> in json format

        if (data['type'] == 'confirmation'):#if VK server request confirmation
            confirmation_token = Company.objects.get(vk_group_id=data['group_id']).vk_confirmation_token
            return HttpResponse(confirmation_token, content_type="text/plain", status=200)

        if (data['type'] == 'message_new'):# if VK server send a message
            token = Company.objects.get(vk_group_id=data['group_id']).vk_access_token
            create_answer(data['object'], token)

    return HttpResponse('ok', content_type="text/plain", status=200)
