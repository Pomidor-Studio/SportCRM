from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import json
from .tasks import do


@csrf_exempt
def google_task_handler(request):

    if request.method == "POST":
        do(request.body)

    return HttpResponse('ok', content_type="text/plain", status=200)

