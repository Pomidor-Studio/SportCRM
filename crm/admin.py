from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Attendance, Client, ClientSubscriptions, Coach, Event, Location,
    SubscriptionsType, User,
)

admin.site.register(Client)
admin.site.register(SubscriptionsType)
admin.site.register(ClientSubscriptions)
admin.site.register(Coach)
admin.site.register(Location)
admin.site.register(Event)
admin.site.register(Attendance)
admin.site.register(User, UserAdmin)
