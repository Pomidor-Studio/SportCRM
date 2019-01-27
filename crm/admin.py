from django.contrib import admin

from .models import Client, SubscriptionsType, Coach, Location, ClientSubscriptions, Event, Attendance

admin.site.register(Client)
admin.site.register(SubscriptionsType)
admin.site.register(ClientSubscriptions)
admin.site.register(Coach)
admin.site.register(Location)
admin.site.register(Event)
admin.site.register(Attendance)



