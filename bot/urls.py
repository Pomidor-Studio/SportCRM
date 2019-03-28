from django.conf.urls import url
from django.urls import path, include

from . import views

app_name = 'bot'

messages_urls = ([
    path('', views.IgnoranceList.as_view(), name='list'),
    path(
        '<uuid:uuid>/',
        views.MessageTemplateEdit.as_view(),
        name='template-edit'
    ),
    path(
        '<uuid:uuid>/reset/',
        views.ResetMessageTemplate.as_view(),
        name='template-reset'
    ),
], 'messages')

bot_urls = ([
    url('tasks', views.tasks, name='tasks'),
    url('', views.gl, name='gl'),
], 'bot')

urlpatterns = [
    path('bot/', include(bot_urls)),
    path('messages/', include(messages_urls)),
]
