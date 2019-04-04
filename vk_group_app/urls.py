from django.urls import path

from . import views

urlpatterns = [
    path('vk_group_app/', views.VkPageView.as_view(), name='vk-app-frame'),
    path('vk_group_app/mark/', views.MarkClient.as_view(), name='mark-client'),
]
