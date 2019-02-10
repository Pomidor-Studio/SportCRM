from django.urls import path

from .views import (
    ClientUpdateView,
    ClientDeleteView,
    ClientCreateView,
    SubscriptionsListView,
    SubscriptionUpdateView,
    SubscriptionDeleteView,
    SubscriptionCreateView,
    ClientSubscriptionCreateView,
    ClientSubscriptionUpdateView,
    ClientSubscriptionDeleteView,
    AttendanceCreateView,
    AttendanceDelete,
    ExtendSubscription,
    EventList,
    EventCreateView,
    EventUpdateView,
    EventDeleteView,
    EventDetailView,
    EventAttendanceCreateView,
)

from . import views

app_name = 'crm'
urlpatterns = [
    path('', views.base, name='base'),
    path('clients/', views.ClientsListView.as_view(), name='clients'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('clients/new/', ClientCreateView.as_view(), name='client-new'),
    path('clients/<int:pk>/update/', ClientUpdateView.as_view(), name='client-update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client-delete'),
    path('clients/<int:client_id>/addsubscription/', ClientSubscriptionCreateView.as_view(),
         name='clientsubscription-new'),
    path('clients/<int:client_id>/addattendance/', AttendanceCreateView.as_view(), name='attendance-new'),

    path('subscriptions/', SubscriptionsListView.as_view(), name='subscriptions'),
    path('subscriptions/<int:pk>/update/', SubscriptionUpdateView.as_view(), name='subscription-update'),
    path('subscriptions/<int:pk>/delete/', SubscriptionDeleteView.as_view(), name='subscription-delete'),
    path('subscriptions/new/', SubscriptionCreateView.as_view(), name='subscription-new'),

    path('clientsubscriptions/<int:pk>/update', ClientSubscriptionUpdateView.as_view(), name='clientsubscription-update'),
    path('clientsubscriptions/<int:pk>/delete', ClientSubscriptionDeleteView.as_view(), name='clientsubscription-delete'),
    path('clientsubscriptions/<int:pk>/extend', ExtendSubscription, name='clientsubscription-extend'),

    path('adattendance/<int:pk>/delete/', AttendanceDelete.as_view(), name='attendance-delete'),

    path('events/', EventList.as_view(), name='event-list'),
    path('events/create/', EventCreateView.as_view(), name='event-create'),
    path('events/<int:pk>/update', EventUpdateView.as_view(), name='event-update'),
    path('events/<int:pk>/delete', EventDeleteView.as_view(), name='event-delete'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('events/<int:event_id>/addattendance/', EventAttendanceCreateView.as_view(), name='event-attendance-new'),

    path('eventclass/', views.EventClassList.as_view(), name='eventclass_list'),
    path('eventclass/create/', views.eventclass_view, name='eventclass_create'),
    path('eventclass/<int:pk>/update/', views.eventclass_view, name='eventclass_update'),
    path('eventclass/<int:pk>/delete/', views.EventClassDelete.as_view(), name='eventclass_delete'),

    path('eventclass/<int:event_class_id>/<int:year>/<int:month>/<int:day>/', views.event_date_view, name='class-event-date'),
    path('eventclass/<int:event_class_id>/<int:year>/<int:month>/<int:day>/mark/', views.event_mark_view, name='event-attendance-mark'),

    path('eventcalendar/<int:pk>/', views.eventcalendar, name='event-calendar'),

]
