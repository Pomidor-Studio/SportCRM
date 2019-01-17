from django.urls import path

from .views import (
    ClientUpdateView,
    ClientDeleteView,
    ClientCreateView,
    SubscriptionsListView,
    SubscriptionUpdateView,
    SubscriptionDeleteView,
    SubscriptionCreateView,
    ClientSubscriptionCreateView
)
from . import views

app_name = 'crm'
urlpatterns = [
    path('', views.base, name='base'),
    path('clients/', views.ClientsListView.as_view(), name='clients'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('eventclass/', views.EventClassList.as_view(), name='eventclass_list'),
    path('eventclass/create/', views.EventClassCreate.as_view(), name='eventclass_create'),
    path('eventclass/<int:pk>/update/', views.EventClassUpdate.as_view(), name='eventclass_update'),
    path('eventclass/<int:pk>/delete/', views.EventClassDelete.as_view(), name='eventclass_delete'),
    path('clients/new/', ClientCreateView.as_view(), name='client-new'),
    path('clients/<int:pk>/update/', ClientUpdateView.as_view(), name='client-update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client-delete'),
    path('subscriptions/', SubscriptionsListView.as_view(), name='subscriptions'),
    path('subscriptions/<int:pk>/update/', SubscriptionUpdateView.as_view(), name='subscription-update'),
    path('subscriptions/<int:pk>/delete/', SubscriptionDeleteView.as_view(), name='subscription-delete'),
    path('subscriptions/new/', SubscriptionCreateView.as_view(), name='subscription-new'),
    path('clients/<int:client_id>/addsubscription/', ClientSubscriptionCreateView.as_view(), name='clientsubscription-new'),
]
