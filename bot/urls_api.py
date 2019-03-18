from django.urls import path

from bot.views import ToggleIgnorance

urlpatterns = [
    path(
        'messages/<str:type>/toggle/',
        ToggleIgnorance.as_view(),
        name='messages-toggle'
    ),
]
