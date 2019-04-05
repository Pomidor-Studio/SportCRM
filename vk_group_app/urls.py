from django.urls import path

from . import views

urlpatterns = [
    path('vk_group_app/', views.VkPageView.as_view(), name='vk-app-frame'),
    path('vk_group_app/mark/', views.MarkClient.as_view(), name='mark-client'),
    path(
        'vk_group_app/unmark/',
        views.UnMarkClient.as_view(),
        name='unmark-client'
    ),
    path(
        'vk_group_app/bot-params/',
        views.CompanyBotParams.as_view(),
        name='bot-params'
    ),
]
