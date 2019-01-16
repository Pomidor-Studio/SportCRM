from django.urls import path

from crm.views import (
    ClientUpdateView,
    ClientDeleteView,
    ClientCreateView,
    SubscriptionsListView,
    SubscriptionUpdateView,
    SubscriptionDeleteView,
    SubscriptionCreateView,
    ClientSubscriptionCreateView)
from . import views

app_name = 'crm'
urlpatterns = [
    path('', views.home, name='crm-home'),
    path('clients/', views.ClientsListView.as_view(), name='clients'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='crm-client-detail'),
    path('eventclass/', views.EventClassList.as_view(), name='eventclass_list'),
    path('eventclass/create/', views.EventClassCreate.as_view(), name='eventclass_create'),
    path('eventclass/<int:pk>/update/', views.EventClassUpdate.as_view(), name='eventclass_update'),
    path('eventclass/<int:pk>/delete/', views.EventClassDelete.as_view(), name='eventclass_delete'),
    path('clients/new/', ClientCreateView.as_view(), name='crm-client-new'),
    path('clients/<int:pk>/update/',
         ClientUpdateView.as_view(), name='crm-client-update'),
    path('clients/<int:pk>/delete/',
         ClientDeleteView.as_view(), name='crm-client-delete'),

    path('subscriptions/', SubscriptionsListView.as_view(),
         name='crm-subscriptions'),
    path('subscriptions/<int:pk>/update/',
         SubscriptionUpdateView.as_view(), name='crm-subscription-update'),
    path('subscriptions/<int:pk>/delete/',
         SubscriptionDeleteView.as_view(), name='crm-subscription-delete'),
    path('subscriptions/new/', SubscriptionCreateView.as_view(),
         name='crm-subscription-new'),

    path(r'^add-client-subscription/(?P<client>\d+)/$', ClientSubscriptionCreateView.as_view(),
         name='crm-clientsubscription-new'),

]
