from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'bot'

urlpatterns = [
    url('bot/', views.gl, name='gl'),
    path('messages/', views.IgnoranceList.as_view(), name='messages')
]

