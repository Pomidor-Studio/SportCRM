from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError

import bot.api.cron.cron_client_events
import bot.api.cron.manager_events


def tasks(request):
    modules = {
        bot.api.cron.cron_client_events,
        bot.api.cron.manager_events
    }
    method_to_call = None

    try:
        param = request.GET['param']
    except MultiValueDictKeyError:
        return HttpResponse(status=400)

    for module in modules:
        if hasattr(module, param):
            method_to_call = getattr(module, param)
            break

    if method_to_call is None:
        return HttpResponse(status=400)

    method_to_call()

    return HttpResponse(status=200)
