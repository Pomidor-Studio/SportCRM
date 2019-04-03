import datetime
from typing import Optional

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.template.response import SimpleTemplateResponse
from django.urls import resolve, reverse
from django.utils.safestring import mark_safe
from django_multitenant.utils import set_current_tenant

from crm.models import Company


def get_user_company(user) -> Optional[Company]:
    if isinstance(user, AnonymousUser):
        return None
    elif user is None:
        return None
    elif user.is_manager or user.is_coach:
        return user.company

    return None


class SetTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        set_current_tenant(get_user_company(request.user))

        response = self.get_response(request)

        set_current_tenant(None)
        # Code to be executed for each request/response after
        # the view is called.

        return response


class CoachInfoMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_anonymous:
            # Don't early save response to variable, as may be added message
            return self.get_response(request)

        if user.is_coach:
            if not user.has_usable_password() or not user.vk_id:
                reset_url = reverse('crm:accounts:password-reset-confirm')
                vk_attach_url = reverse('crm:accounts:profile')
                messages.info(
                    request,
                    mark_safe(
                        f'У вас не установлен пароль или не сделана привязка '
                        f'аккаунта к Вконтакте. На этой странице можно '
                        f'<a href="{reset_url}">сбросить пароль</a>, а на '
                        f'странице <a href="{vk_attach_url}">профиля</a> можно '
                        f'привязать аккаунт к Вконтакте, и входить без пароля.'
                    )
                )

        return self.get_response(request)


class TimedAccessMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        company = get_user_company(request.user)

        safe_url = (
            'crm:accounts:login',
            'crm:accounts:logout',
            'admin',
            'social'
        )
        rs = resolve(request.path)
        is_safe_url = any(rs.view_name.startswith(x) for x in safe_url)

        if not is_safe_url and company and company.active_to:
            today = datetime.date.today()
            closed_date = today + datetime.timedelta(days=14)

            # Do early exit if company use period ended
            if company.active_to < today:
                return SimpleTemplateResponse(
                    'crm/company/inactive.html', {
                        'user': request.user,
                        'company': company
                    }
                ).render()
            # Add notification if remains less than two weeks to the end
            # of active period
            elif today < company.active_to < closed_date:
                npe = request.session.get('notify_period_end')
                is_today_notify = False
                if npe:
                    try:
                        is_today_notify = (
                            datetime.datetime
                            .strptime(npe, '%d.%m.%Y').date() == today
                        )
                    except ValueError:
                        pass

                if not npe or not is_today_notify:
                    messages.info(
                        request,
                        f'Скоро ({company.active_to:%d.%m.%Y}) закончится '
                        f'доступный период использования'
                    )
                    request.session['notify_period_end'] = \
                        today.strftime('%d.%m.%Y')

        response = self.get_response(request)
        return response
