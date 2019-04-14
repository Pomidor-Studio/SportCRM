import rules

# Detail about rule system: https://github.com/dfunckt/django-rules
from django.conf import settings
from django_multitenant.utils import get_current_tenant

from crm.models import Event, SubscriptionsType


@rules.predicate
def is_manager(user) -> bool:
    return user.is_manager


@rules.predicate
def is_coach(user) -> bool:
    return user.is_coach


@rules.predicate
def is_coach_event(user, event: Event):
    return event.event_class.coach == user.coach


@rules.predicate
def is_open_event(user, event: Event):
    return not event.is_closed


@rules.predicate
def is_not_one_time_sub(user, obj: SubscriptionsType):
    return not obj.one_time if obj else True


@rules.predicate
def is_not_hidden_managers_in_company(user) -> bool:
    return (
        get_current_tenant().id not in
        settings.DISABLE_MANAGER_PERMISSION_FOR_COMPANIES
    )


is_logged_manager = rules.is_authenticated & is_manager
is_logged_coach = rules.is_authenticated & is_coach
is_logged_personnel = rules.is_authenticated & (is_manager | is_coach)

is_editable_by_coach = is_logged_coach & is_coach_event
is_editable_event = (is_logged_manager | is_editable_by_coach) & is_open_event

# Generic permission, can be used, until detailed are needed
rules.add_perm('is_manager', is_logged_manager)
rules.add_perm('is_coach', is_logged_coach)

rules.add_perm('company.edit', is_logged_manager)

rules.add_perm('client-balance.add', is_logged_personnel)

rules.add_perm('client', is_logged_personnel)
rules.add_perm('client.add', is_logged_personnel)
rules.add_perm('client.edit', is_logged_personnel)
rules.add_perm('client.delete', is_logged_personnel)

rules.add_perm('coach', is_logged_personnel)
rules.add_perm('coach.view_detail', is_logged_manager)
rules.add_perm('coach.view_archive', is_logged_manager)
rules.add_perm('coach.add', is_logged_manager)
rules.add_perm('coach.edit', is_logged_manager)
rules.add_perm('coach.delete', is_logged_manager)
rules.add_perm('coach.undelete', is_logged_manager)

rules.add_perm(
    'manager', is_logged_personnel & is_not_hidden_managers_in_company)
rules.add_perm(
    'manager.view_detail',
    is_logged_manager & is_not_hidden_managers_in_company
)
rules.add_perm(
    'manager.add', is_logged_manager & is_not_hidden_managers_in_company)
rules.add_perm(
    'manager.edit', is_logged_manager & is_not_hidden_managers_in_company)
rules.add_perm(
    'manager.delete', is_logged_manager & is_not_hidden_managers_in_company)

rules.add_perm('event_class', is_logged_manager)
rules.add_perm('event_class.add', is_logged_manager)
rules.add_perm('event_class.edit', is_logged_manager)
rules.add_perm('event_class.delete', is_logged_manager)

rules.add_perm('event', is_logged_personnel)
rules.add_perm('event.manipulate', is_editable_event)
rules.add_perm('event.mark-attendance', is_editable_event)
rules.add_perm('event.cancel', is_editable_event)
rules.add_perm('event.activate', is_editable_event)
rules.add_perm('event.close', is_logged_manager | is_editable_by_coach)
rules.add_perm('event.open', is_logged_manager | is_editable_by_coach)

rules.add_perm('attendance.delete', is_logged_personnel)

rules.add_perm('location', is_logged_manager)
rules.add_perm('location.add', is_logged_manager)
rules.add_perm('location.edit', is_logged_manager)
rules.add_perm('location.delete', is_logged_manager)
rules.add_perm('location.undelete', is_logged_manager)
rules.add_perm('location.view_archive', is_logged_manager)

rules.add_perm('subscription', is_logged_manager)
rules.add_perm('subscription.view_archive', is_logged_manager)
rules.add_perm('subscription.add', is_logged_manager)
rules.add_perm('subscription.edit', is_logged_manager & is_not_one_time_sub)
rules.add_perm('subscription.extend', is_logged_manager)
rules.add_perm('subscription.delete', is_logged_manager)
rules.add_perm('subscription.undelete', is_logged_manager)

rules.add_perm('client_subscription.extend', is_logged_manager)
rules.add_perm('client_subscription.delete', is_logged_manager)
rules.add_perm('client_subscription.edit', is_logged_manager)

rules.add_perm('client_subscription.sale', is_logged_personnel)

rules.add_perm('report.list', is_logged_manager)
rules.add_perm('report.events', is_logged_manager)
