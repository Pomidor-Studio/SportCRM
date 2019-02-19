from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    UserChangeForm, UserCreationForm, UsernameField,
)

from .models import (
    Attendance, Client, ClientSubscriptions, Coach, Company, Event, Location,
    Manager, SubscriptionsType, User,
)


class TenantUserCreateForm(UserCreationForm):
    class Meta:
        models = User
        fields = ('username', 'company')
        field_classes = {'username': UsernameField}


class TenantUserChangeForm(UserChangeForm):
    class Meta:
        models = User
        fields = '__all__'
        field_classes = {'username': UsernameField}


@admin.register(User)
class TenantUserAdmin(UserAdmin):
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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    fields = ('display_name', 'name')
    readonly_fields = ('name',)
    list_display = ('display_name',)


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')


admin.site.register(Client)
admin.site.register(SubscriptionsType)
admin.site.register(ClientSubscriptions)
admin.site.register(Location)
admin.site.register(Event)
admin.site.register(Attendance)
