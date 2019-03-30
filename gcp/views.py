from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import json
from .tasks import do


@csrf_exempt
def google_task_handler(request):

    if request.method == "POST":
        result:str = do(request.body)
        return HttpResponse(result, content_type="text/plain", status=200)
    else:
        return HttpResponse('Only POST alloyed', content_type="text/plain", status=405)


def warm_up(request):
    return HttpResponse('warm up', content_type="text/plain", status=200)
