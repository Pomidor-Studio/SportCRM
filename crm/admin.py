from django.contrib import admin

from .models import Client, SubscriptionsType, Coach, Location


admin.site.register(Client)
admin.site.register(SubscriptionsType)
admin.site.register(Coach)
admin.site.register(Location)

