from django.conf.urls import url

from . import views

urlpatterns = [
     url('vk_group_app/', views.EventSingUp.as_view(), name='vk-app-frame'),
]
