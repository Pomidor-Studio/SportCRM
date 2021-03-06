"""Create a task for a given queue with an arbitrary payload."""
import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from django_multitenant.utils import set_current_tenant, get_current_tenant
from google.cloud import tasks_v2beta3

import bot.api.messageHandler
import bot.tasks
from crm.models import Company


def enqueue(method: str, *args, **kwargs):

    payload = {'method': method,
               'args': args,
               'kwargs': kwargs,
               'company_id': get_current_tenant().id
               }

    # The API expects a payload of type bytes.
    json_payload = json.dumps(payload)

    converted_payload = json_payload.encode()

    if settings.USE_GOOGLE_TASKS:

        project = settings.GCP_TASK_PROJECT
        queue = settings.GCP_TASK_QUEUE
        location = settings.GCP_TASK_LOCATION

        client = tasks_v2beta3.CloudTasksClient()

        # Construct the fully qualified queue name.
        parent = client.queue_path(project, location, queue)

        # Construct the request body.
        task = {
            'app_engine_http_request': {  # Specify the type of request.
                'http_method': 'POST',
                'relative_uri': '/google_task_handler/'
            }
        }
        # Add the payload to the request.
        task['app_engine_http_request']['body'] = converted_payload

        # Use the client to build and send the task.
        response = client.create_task(parent, task)
    else:
        do_result = do(converted_payload)
        if not do_result == 'OK':
            raise RuntimeError(f'DO result: {do_result}')


def do(body_payload: bytes) -> str:

    payload = json.loads(body_payload.decode())
    company_id = payload['company_id']
    method = payload['method']
    if not method:
        return 'ERROR: no method in payload'

    args = payload['args']
    kwargs = payload['kwargs']
    modules = {bot.tasks, bot.api.messageHandler}
    if company_id:
        company = get_object_or_404(Company, pk=company_id)
        set_current_tenant(company)

    method_to_call = None

    for module in modules:
        if hasattr(module, method):
            method_to_call = getattr(module, method)

    if method_to_call:
        method_to_call(*args, **kwargs)
        return 'OK'
    else:
        return f'ERROR: no method "{method}" in modules'


