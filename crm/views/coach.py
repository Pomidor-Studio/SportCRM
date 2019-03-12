from datetime import timedelta

from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from rest_framework.fields import DateField
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rules.contrib.views import PermissionRequiredMixin

from crm.models import EventClass
from crm.serializers import CalendarEventSerializer


class HomePage(PermissionRequiredMixin, TemplateView):
    permission_required = 'is_coach'
    template_name = 'crm/coach/home.html'

    def notify_vk(self):
        if not self.request.user.has_vk_auth:
            reset_url = reverse('crm:accounts:profile')
            messages.info(
                self.request,
                mark_safe(
                    f'Вы еще не привязали ваш аккаунт к VK. Это можно сделать '
                    f'на странице <a href="{reset_url}">профиля</a>.'
                )
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['coach'] = self.request.user.coach
        return context

    def get(self, request, *args, **kwargs):
        self.notify_vk()

        return super().get(request, *args, **kwargs)


class ApiCalendar(ListAPIView):
    serializer_class = CalendarEventSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        first_day = timezone.now().replace(day=1).date()
        start = DateField().to_internal_value(
            self.request.query_params.get('start')
        ) or first_day

        end = DateField().to_internal_value(
            self.request.query_params.get('end')
        ) or (first_day + timedelta(days=31))

        events = []
        for ec in EventClass.objects.filter(
            Q(coach=self.request.user.coach) &
            Q(date_from__lte=end) &
            (Q(date_to__gte=start) | Q(date_to__isnull=True))
        ):
            events.extend(list(ec.get_calendar(start, end).values()))

        return events
