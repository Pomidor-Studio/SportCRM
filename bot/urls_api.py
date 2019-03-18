from django.urls import path

from bot.views import ToggleIgnorance

urlpatterns = [
    path(
        'messages/<uuid:uuid>/toggle/',
        ToggleIgnorance.as_view(),
        name='messages-toggle'
    ),
]
