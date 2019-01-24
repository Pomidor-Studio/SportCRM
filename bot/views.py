# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from bot.api.settings import *
from bot.api.messageHandler import create_answer

import json, vk

"""
Using VK Callback API version 5.5
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
        if (data['secret'] == secret_key):# if json request contain secret key and it's equal my secret key
            if (data['type'] == 'confirmation'):# if VK server request confirmation

                return HttpResponse(confirmation_token, content_type="text/plain", status=200)
            if (data['type'] == 'message_new'):# if VK server send a message

                create_answer(data['object'], token)
                return HttpResponse('ok', content_type="text/plain", status=200)