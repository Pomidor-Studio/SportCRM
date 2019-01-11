from django.contrib import admin

from .models import clients, subscriptions


admin.site.register(clients)
admin.site.register(subscriptions)
