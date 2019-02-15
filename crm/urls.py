from django.contrib.auth import views as auth_views
from django.urls import include, path

from crm.views import coach as coach_views, auth as scrm_auth_views
from crm.views.manager import (
    core as manager_core_views,
    coach as manager_coach_views,
    client as manager_client_views,
    subscription as manager_subs_views,
    event as manager_event_views,
)
from .views import (
    ClientSubscriptionUpdateView,
    ClientSubscriptionDeleteView,
    AttendanceDelete,
    ExtendSubscription,
)

from . import views

app_name = 'crm'

coach_urlpatterns = ([
    path('', coach_views.HomePage.as_view(), name='home')
], 'coach')

auth_urlpatterns = ([
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='crm/auth/login.html'),
        name='login'
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'redirect/',
        scrm_auth_views.SportCrmLoginRedirectView.as_view(),
        name='login-redirect'
    ),
], 'accounts')

manager_coach_urlpatterns = ([
    path('', manager_coach_views.List.as_view(), name='list'),
    path('<int:pk>/', manager_coach_views.Detail.as_view(), name='detail'),
    path('new/', manager_coach_views.Create.as_view(), name='new'),
    path(
        '<int:pk>/update/',
        manager_coach_views.Update.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_coach_views.Delete.as_view(),
        name='delete'
    )
], 'coach')

manager_clients_urlpatterns = ([
    path('', manager_client_views.List.as_view(), name='list'),
    path('<int:pk>/', manager_client_views.Detail.as_view(), name='detail'),
    path('new/', manager_client_views.Create.as_view(), name='new'),
    path(
        '<int:pk>/update/',
        manager_client_views.Update.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_client_views.Delete.as_view(),
        name='delete'
    ),
    path(
        '<int:client_id>/add-subscription/',
        manager_client_views.AddSubscription.as_view(),
        name='new-subscription'
    ),
    path(
        '<int:client_id>/add-attendance/',
        manager_client_views.AddAttendance.as_view(),
        name='new-attendance'
    ),
], 'client')

manager_subscriptions_urlpatterns = ([
    path('', manager_subs_views.List.as_view(), name='list'),
    path(
        '<int:pk>/update/',
        manager_subs_views.Update.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_subs_views.Delete.as_view(),
        name='delete'
    ),
    path('new/', manager_subs_views.Create.as_view(), name='new'),
], 'subscription')

manager_events_urlpatterns = ([
    path('', manager_event_views.List.as_view(), name='list'),
    path('new/', manager_event_views.Create.as_view(), name='new'),
    path(
        '<int:pk>/update/',
        manager_event_views.Update.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_event_views.Delete.as_view(),
        name='delete'
    ),
    path(
        '<int:pk>/',
        manager_event_views.Detail.as_view(),
        name='detail'
    ),
    path(
        '<int:event_id>/add-attendance/',
        manager_event_views.EventAttendanceCreate.as_view(),
        name='new-attendance'
    ),
], 'event')

manager_urlpatterns = ([
    path('', manager_core_views.Home.as_view(), name='home'),
    path('coach/', include(manager_coach_urlpatterns)),
    path('clients/', include(manager_clients_urlpatterns)),
    path('subscriptions/', include(manager_subscriptions_urlpatterns)),
    path('events/', include(manager_events_urlpatterns)),
], 'manager')

urlpatterns = [
    path('', scrm_auth_views.SportCrmLoginRedirectView.as_view()),
    path('accounts/', include(auth_urlpatterns)),
    path('coach/', include(coach_urlpatterns)),
    path('manager/', include(manager_urlpatterns)),

    path('clientsubscriptions/<int:pk>/update', ClientSubscriptionUpdateView.as_view(), name='clientsubscription-update'),
    path('clientsubscriptions/<int:pk>/delete', ClientSubscriptionDeleteView.as_view(), name='clientsubscription-delete'),
    path('clientsubscriptions/<int:pk>/extend', ExtendSubscription, name='clientsubscription-extend'),

    path('adattendance/<int:pk>/delete/', AttendanceDelete.as_view(), name='attendance-delete'),

    path('eventclass/', views.EventClassList.as_view(), name='eventclass_list'),
    path('eventclass/create/', views.eventclass_view, name='eventclass_create'),
    path('eventclass/<int:pk>/update/', views.eventclass_view, name='eventclass_update'),
    path('eventclass/<int:pk>/delete/', views.EventClassDelete.as_view(), name='eventclass_delete'),

    path('eventclass/<int:event_class_id>/<int:year>/<int:month>/<int:day>/', views.event_date_view, name='class-event-date'),
    path('eventclass/<int:event_class_id>/<int:year>/<int:month>/<int:day>/mark/', views.event_mark_view, name='event-attendance-mark'),

    path('eventcalendar/<int:pk>/', views.eventcalendar, name='event-calendar'),

]
