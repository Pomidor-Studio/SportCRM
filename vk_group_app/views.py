from datetime import date, datetime, timedelta

from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import TemplateView
from django_multitenant.utils import set_current_tenant
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response

from contrib.vk_utils import get_vk_user_info
from crm.models import Attendance, Client, Company, Event, EventClass
from vk_group_app.serializers import VkActionSerializer
from vk_group_app.utils import signed_clients_display


@method_decorator(xframe_options_exempt, name='dispatch')
class VkPageView(TemplateView):
    vk_group_id: int = 0
    vk_user_id: int = None

    def get(self, request, *args, **kwargs):
        # iframe init params: https://vk.com/dev/apps_init

        try:
            self.vk_group_id = int(request.GET.get('group_id', 0))
        except (ValueError, KeyError, TypeError):
            pass

        # viewer_id is always present
        self.vk_user_id = int(request.GET['viewer_id'])
        self.app_id = int(request.GET['api_id'])

        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        if self.vk_group_id != 0:
            return 'vk_group_app/vk_sign_up.html'
        else:
            return 'vk_group_app/vk_app_promo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.vk_group_id != 0:
            context.update(self.get_user_page_context())
        else:
            context.update(self.get_app_page_context())

        return context

    def get_app_page_context(self):
        return {
            'app_id': self.app_id
        }

    def get_user_page_context(self):
        try:
            company = self.setup_tenant()
        except ValueError:
            return {}

        client = Client.objects.filter(vk_user_id=self.vk_user_id).first()
        day_start = date.today()
        day_end = day_start + timedelta(weeks=1)

        # Prepare events
        events = []
        for ec in EventClass.objects.in_range(day_start, day_end):
            events.extend(list(ec.get_calendar(day_start, day_end).values()))
        events = sorted(
            events, key=lambda x: datetime.combine(x.date, x.start_time))

        # Prepare event class one time visit price
        ec_otv_price = {}
        for event in events:
            ec_id = event.event_class_id
            if ec_id in ec_otv_price:
                continue

            ec_otv_price[ec_id] = event.event_class.otv_price

        # Prepare count of clients signed for one event
        a_count = (
            Attendance.objects
            .filter(event__in=[x.id for x in events], signed_up=True)
            .annotate(client_count=Count('event'))
            .values('event_id', 'client_count')
        )
        event_signed_count = {
            x['event_id']: x['client_count'] for x in a_count
        }

        # Find events where this client is marked
        my_events = []
        if client:
            my_events = Attendance.objects.filter(
                event__in=[x.id for x in events],
                signed_up=True,
                client=client
            ).values_list('event_id', flat=True)

        return {
            'vk_id': self.vk_user_id,
            'vk_group': self.vk_group_id,
            'client': client,
            'my_events': my_events,
            'events': events,
            'ec_otv_price': ec_otv_price,
            'event_signed_count': event_signed_count
        }

    def setup_tenant(self):
        try:
            company = Company.objects.get(vk_group_id=self.vk_group_id)
        except Company.DoesNotExist:
            raise ValueError()

        set_current_tenant(company)
        return company


class EventMixin:
    def get_event(self, serializer):
        event_date = date(
            serializer.validated_data['year'],
            serializer.validated_data['month'],
            serializer.validated_data['day']
        )
        event = Event.objects.get_or_virtual(
            serializer.validated_data['eventClassId'], event_date)
        if not event.id:
            event.save()

        return event


class ClientMixin:
    def get_client(self, serializer) -> Client:
        client = Client.objects.filter(
            vk_user_id=serializer.validated_data['vkId']).first()
        if not client:
            client = self.create_client(serializer)
        return client

    def create_client(self, serializer):
        vk_id = serializer.validated_data['vkId']
        client = Client.objects.create(vk_user_id=vk_id)
        info = get_vk_user_info(vk_id)[vk_id]
        client.name = f'{info["first_name"]} {info["last_name"]}'
        bdate = info.get('bdate')
        if bdate:
            try:
                client.birthday = datetime.strptime(bdate, '%d.%m.%Y')
            except ValueError:
                pass
        client.save()
        return client

    def set_tenant(self, serializer):
        company = Company.objects.get(
            vk_group_id=serializer.validated_data['vkGroup'])
        if not company:
            raise ValueError('No company found for vk group')

        set_current_tenant(company)


class MarkClient(ClientMixin, EventMixin, GenericAPIView):

    serializer_class = VkActionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.set_tenant(serializer)
            client = self.get_client(serializer)
            event: Event = self.get_event(serializer)
            client.signup_for_event(event)
        except Exception as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'success': True,
            'signedCount': signed_clients_display(event.signed_up_clients)
        }, status=status.HTTP_201_CREATED)


class UnMarkClient(ClientMixin, EventMixin, CreateAPIView):
    serializer_class = VkActionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.set_tenant(serializer)
            client = self.get_client(serializer)
            event: Event = self.get_event(serializer)
            client.cancel_signup_for_event(event)
        except Exception as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'success': True,
            'signedCount': signed_clients_display(event.signed_up_clients)
        }, status=status.HTTP_201_CREATED)
