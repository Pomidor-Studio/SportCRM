from django.contrib import admin

from .models import Client, Subscription


admin.site.register(Client)
admin.site.register(Subscription)
