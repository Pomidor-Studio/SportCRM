from django.contrib import admin

from .models import Client, SubscriptionsType, Coach, Location, ClientSubscriptions

admin.site.register(Client)
admin.site.register(SubscriptionsType)
admin.site.register(ClientSubscriptions)
admin.site.register(Coach)
admin.site.register(Location)

