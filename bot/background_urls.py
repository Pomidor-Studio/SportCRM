from django.urls import path
from .background_views import tasks

urlpatterns = [
    path('bot/tasks', tasks, name='tasks'),
]
