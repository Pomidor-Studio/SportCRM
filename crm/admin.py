from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    UserChangeForm, UserCreationForm, UsernameField,
)
from reversion_compare.admin import CompareVersionAdmin
from social_django.admin import (
    UserSocialAuthOption, NonceOption,
    AssociationOption,
)
from social_django.models import UserSocialAuth, Nonce, Association

from crm import models


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
    list_display = ('get_manager_full_name', 'user', 'company')

    def get_manager_full_name(self, obj: models.Manager):
        return obj.user.get_full_name()


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


@admin.register(models.ClientSubscriptions)
class ClientSubscriptionsAdmin(CompareVersionAdmin):
    pass


@admin.register(models.ExtensionHistory)
class ExtensionHistoryAdmin(CompareVersionAdmin):
    pass


@admin.register(models.Event)
class EventAdmin(CompareVersionAdmin):
    pass


@admin.register(models.Attendance)
class AttendanceAdmin(CompareVersionAdmin):
    pass
