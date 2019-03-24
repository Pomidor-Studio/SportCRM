from datetime import date, timedelta

from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import TemplateView
from django_multitenant.utils import set_current_tenant

from crm.models import Company, Client, EventClass


@method_decorator(xframe_options_exempt, name='dispatch')
class EventSingUp(TemplateView):
    template_name = 'vk_group_app/vk_sign_up.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vk_group_id = self.request.GET['group_id']
        vk_user_id = self.request.GET['viewer_id']

        try:
            company = Company.objects.get(vk_group_id=vk_group_id)
        except Company.DoesNotExist:
            return context

        set_current_tenant(company)

        try:
            client = Client.objects.get(vk_user_id=vk_user_id)
            result = f'Это {company.display_name} и {client.name}'
        except Client.DoesNotExist:
            result = f'Это {company.display_name} и незарегистрированный клиент'

        context['result'] = result
        start = date.today()
        end = start + timedelta(weeks=1)
        events = []
        for ec in EventClass.objects.filter(
            Q(date_from__lte=end) &
            (Q(date_to__gte=start) | Q(date_to__isnull=True))
        ):
            events.extend(list(ec.get_calendar(start, end).values()))
        context['events'] = events
        return context
