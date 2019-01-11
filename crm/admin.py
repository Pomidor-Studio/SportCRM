from django.contrib import admin

from .models import Client, SubscriptionsType


admin.site.register(Client)
admin.site.register(SubscriptionsType)
