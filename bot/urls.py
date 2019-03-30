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

urlpatterns = [
    path('bot/gl', views.gl),
    path('messages/', include(messages_urls)),
]
