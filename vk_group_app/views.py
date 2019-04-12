from datetime import date, datetime, timedelta

from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import TemplateView
from django_multitenant.utils import set_current_tenant, get_current_tenant
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from gcp.tasks import enqueue

from contrib.vk_utils import get_vk_user_info
from crm.models import Attendance, Client, Company, Event, EventClass
from vk_group_app.const import VK_USER_GUEST, VK_USER_ADMIN
from vk_group_app.serializers import (
    VkActionSerializer,
    VkAdminOptionsSerializer,
)
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
        self.vk_user_type = int(request.GET['viewer_type'])

        try:
            self.setup_tenant()
        except ValueError:
            # Request may not have tenant, if it was called from app page or
            # admin launch application for the first time
            pass

        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        # Application is run from group
        if self.vk_group_id != 0:
            # User is not in group
            if self.vk_user_type == VK_USER_GUEST:
                return 'vk_group_app/vk_enter_in_group.html'
            else:
                return 'vk_group_app/vk_sign_up.html'
        else:
            return 'vk_group_app/vk_app_promo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.vk_group_id != 0:
            # User is not in group
            if self.vk_user_type == VK_USER_GUEST:
                context.update(self.get_enter_page_context())
            else:
                context.update(self.get_user_page_context())
                if self.vk_user_type == VK_USER_ADMIN:
                    context.update(self.get_admin_page_context())
        else:
            context.update(self.get_app_page_context())

        return context

    def get_app_page_context(self):
        return {
            'app_id': self.app_id
        }

    def get_enter_page_context(self):
        return {
            'vk_group': self.vk_group_id
        }

    def get_admin_page_context(self):
        context_data = {
            'app_id': self.app_id,
            'is_admin': True,
            'has_company': True,
            'has_access_token': False,
            'vk_group': self.vk_group_id
        }
        company = get_current_tenant()
        if company is None:
            context_data['has_company'] = False
        else:
            context_data['has_access_token'] = (
                company.vk_access_token is not None
            )
            context_data['vk_access_token'] = company.vk_access_token
            context_data['vk_confirmation_token'] = \
                company.vk_confirmation_token

        return context_data

    def get_user_page_context(self):
        company = get_current_tenant()
        if company is None:
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
            'is_admin': False,
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


class CompanyMixin:
    def get_company(self, serializer):
        try:
            return Company.objects.get(
                vk_group_id=serializer.validated_data['vkGroup'])
        except Company.DoesNotExist:
            return None

    def set_tenant(self, serializer):
        company = self.get_company(serializer)
        if not company:
            raise ValueError('No company found for vk group')

        set_current_tenant(company)


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


class MarkClient(ClientMixin, CompanyMixin, EventMixin, GenericAPIView):

    serializer_class = VkActionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.set_tenant(serializer)
            client = self.get_client(serializer)
            event: Event = self.get_event(serializer)
            client.signup_for_event(event)
            enqueue('notify_manager_about_signup', event.id, client.id)
        except Exception as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_200_OK
            )

        return Response({
            'success': True,
            'signedCount': signed_clients_display(event.signed_up_clients)
        }, status=status.HTTP_201_CREATED)


class UnMarkClient(ClientMixin, CompanyMixin, EventMixin, CreateAPIView):
    serializer_class = VkActionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.set_tenant(serializer)
            client = self.get_client(serializer)
            event: Event = self.get_event(serializer)
            client.cancel_signup_for_event(event)
            enqueue('notify_manager_about_unsignup', event.id, client.id)
        except Exception as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_200_OK
            )

        return Response({
            'success': True,
            'signedCount': signed_clients_display(event.signed_up_clients)
        }, status=status.HTTP_201_CREATED)


class CompanyBotParams(CompanyMixin, CreateAPIView):
    serializer_class = VkAdminOptionsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = self.get_company(serializer)
        if not company:
            return Response(
                {
                    'success': False,
                    'error': 'Нет компании привязанной к сообществу'
                },
                status=status.HTTP_200_OK
            )

        company.vk_access_token = serializer.validated_data['accessToken']
        company.vk_confirmation_token = serializer.validated_data['botConfirm']
        company.save()

        return Response({'success': True}, status=status.HTTP_200_OK)
