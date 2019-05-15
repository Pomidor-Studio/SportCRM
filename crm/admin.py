from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    UserChangeForm, UserCreationForm, UsernameField,
)
from django.utils.html import format_html
from reversion_compare.admin import CompareVersionAdmin
from social_django.admin import (
    AssociationOption, NonceOption, UserSocialAuthOption,
)
from social_django.models import Association, Nonce, UserSocialAuth

from crm import models
from crm.auth.one_time_login import get_one_time_login_link

# Re-register social auth admin, for purposes of django-reversion integration
admin.site.unregister(UserSocialAuth)
admin.site.unregister(Nonce)
admin.site.unregister(Association)


@admin.register(UserSocialAuth)
class UserSocialAuthAdmin(CompareVersionAdmin, UserSocialAuthOption):
    pass


@admin.register(Nonce)
class NonceAdmin(CompareVersionAdmin, NonceOption):
    pass


@admin.register(Association)
class AssociationAdmin(CompareVersionAdmin, AssociationOption):
    pass

# End of re-register part


@admin.register(models.Company)
class CompanyAdmin(CompareVersionAdmin):
    fields = (
        'name', 'display_name', 'vk_group_id', 'vk_access_token',
        'vk_confirmation_token', 'active_to'
    )
    readonly_fields = ('name',)
    list_display = ('display_name',)


class TenantUserCreateForm(UserCreationForm):
    class Meta:
        models = models.User
        fields = ('username', 'company')
        field_classes = {'username': UsernameField}


class TenantUserChangeForm(UserChangeForm):
    class Meta:
        models = models.User
        fields = '__all__'
        field_classes = {'username': UsernameField}


@admin.register(models.User)
class TenantUserAdmin(CompareVersionAdmin, UserAdmin):
    form = TenantUserChangeForm
    add_form = TenantUserCreateForm
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': ('company',)
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('company',)
        }),
    )


@admin.register(models.Location)
class LocationAdmin(CompareVersionAdmin):
    pass


@admin.register(models.Manager)
class ManagerAdmin(CompareVersionAdmin):
    list_display = (
        'get_manager_full_name', 'user', 'company', 'get_one_time_link'
    )

    def changelist_view(self, request, extra_context=None):
        self.host = request.get_host()
        return super().changelist_view(request, extra_context)

    def get_manager_full_name(self, obj: models.Manager):
        return obj.user.get_full_name()

    def get_one_time_link(self, obj: models.Manager):
        return format_html(
            '<a href="{url}">{url}</a>'.format(
                url=get_one_time_login_link(self.host, obj.user)
            )
        )


@admin.register(models.Coach)
class CoachAdmin(CompareVersionAdmin):
    list_display = ('get_coach_full_name', 'user', 'company')

    def get_coach_full_name(self, obj: models.Coach):
        return obj.user.get_full_name()


@admin.register(models.EventClass)
class EventClassAdmin(CompareVersionAdmin):
    pass


@admin.register(models.DayOfTheWeekClass)
class DayOfTheWeekClassAdmin(CompareVersionAdmin):
    pass


@admin.register(models.SubscriptionsType)
class SubscriptionsTypeAdmin(CompareVersionAdmin):
    pass


@admin.register(models.Client)
class ClientAdmin(CompareVersionAdmin):
    list_display = ('name', 'vk_user_id', 'company')


@admin.register(models.ClientBalanceChangeHistory)
class ClientBalanceChangeHistoryAdmin(CompareVersionAdmin):
    list_display = ('client', 'entry_date', 'reason', 'change_value')


@admin.register(models.ClientSubscriptions)
class ClientSubscriptionsAdmin(CompareVersionAdmin):
    readonly_fields = ('visits_on_by_time', 'subscription', 'client',)
    list_display = ('__str__', 'purchase_date', 'start_date', 'end_date', 'client',)


@admin.register(models.ExtensionHistory)
class ExtensionHistoryAdmin(CompareVersionAdmin):
    pass


@admin.register(models.Event)
class EventAdmin(CompareVersionAdmin):
    pass


@admin.register(models.Attendance)
class AttendanceAdmin(CompareVersionAdmin):
    pass
