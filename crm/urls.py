from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

from crm.views import coach as coach_views, auth as scrm_auth_views
from crm.views.manager import (
    core as manager_core_views,
    coach as manager_coach_views,
    client as manager_client_views,
    subscription as manager_subs_views,
    event as manager_event_views,
    event_class as manager_event_class_views,
    attendance as manager_attendance_views,
    location as manager_locations_views
)

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
    path('profile/', scrm_auth_views.ProfileView.as_view(), name='profile'),
    path(
        'password-change/',
        scrm_auth_views.SportCrmPasswordChangeView.as_view(),
        name='password-change'
    ),
    path(
        'password-reset-confirm/',
        scrm_auth_views.ResetPasswordConfirmView.as_view(),
        name='password-reset-confirm'
    ),
    path(
        'password-reset/',
        scrm_auth_views.ResetPasswordView.as_view(),
        name='password-reset'
    )
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
    ),
    path(
        '<int:pk>/undelete/',
        manager_coach_views.Undelete.as_view(),
        name='undelete'
    )
], 'coach')

manager_client_subs_urlpatterns = ([
    path(
        '<int:pk>/update',
        manager_client_views.SubscriptionUpdate.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete',
        manager_client_views.SubscriptionDelete.as_view(),
        name='delete'
    ),
    path(
        '<int:pk>/extend',
        manager_client_views.SubscriptionExtend.as_view(),
        name='extend'
    ),
], 'subscription')

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
    path(
        'subscription/',
        include(manager_client_subs_urlpatterns)
    )
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
    path(
        '<int:pk>/undelete/',
        manager_subs_views.UnDelete.as_view(),
        name='undelete'
    ),
    path('new/', manager_subs_views.Create.as_view(), name='new'),
], 'subscription')

# TODO: Remove obsolete views and urls
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
    path(
        'report/',
        manager_event_views.Report.as_view(),
        name='report'
    ),
], 'event')

manager_event_urlpatterns = ([
    path(
        '',
        manager_event_class_views.EventByDate.as_view(),
        name='event-by-date'
    ),
    path(
        'mark/',
        manager_event_class_views.MarkEventAttendance.as_view(),
        name='mark-attendance'
    ),
    path(
        'mark/<int:subscription_id>',
        manager_event_class_views.MarkClientAttendance.as_view(),
        name='mark-client-attendance'
    ),
    path(
        'cancel/without-extending/',
        manager_event_class_views.CancelWithoutExtending.as_view(),
        name='cancel-without-extending'
    ),
    path(
        'cancel/with-extending/',
        manager_event_class_views.CancelWithExtending.as_view(),
        name='cancel-with-extending'
    ),
    path(
        'activate/without-revoke/',
        manager_event_class_views.ActivateWithoutRevoke.as_view(),
        name='activate-without-revoke'
    ),
    path(
        'activate/with-revoke/',
        manager_event_class_views.ActivateWithRevoke.as_view(),
        name='activate-with-revoke'
    ),
    path(
        'scan/',
        manager_event_class_views.Scanner.as_view(),
        name='scanner'
    ),
    path(
        'scan/<str:code>/',
        manager_event_class_views.DoScan.as_view(),
        name='do-scan'
    ),
    path(
        'is_closed/',
        manager_event_class_views.IsClosed.as_view(),
        name='is-closed'
    )
], 'event')

manager_event_class_urlpatterns = ([
    path(
        '',
        manager_event_class_views.ObjList.as_view(),
        name='list'
    ),
    path('new/', manager_event_class_views.CreateEdit.as_view(), name='new'),
    path(
        '<int:pk>/update/',
        manager_event_class_views.CreateEdit.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_event_class_views.Delete.as_view(),
        name='delete'
    ),
    path(
        '<int:event_class_id>/<int:year>/<int:month>/<int:day>/',
        include(manager_event_urlpatterns)
    ),
    path(
        '<int:pk>/calendar/',
        manager_event_class_views.Calendar.as_view(),
        name='calendar'),
], 'event-class')

manager_attendance_urlpatterns = ([
    path(
        '<int:pk>/delete/',
        manager_attendance_views.Delete.as_view(),
        name='delete'),
], 'attendance')

manager_locations_urlpatterns = ([
    path(
        '',
        manager_locations_views.ObjList.as_view(),
        name='list'
    ),
    path('new/', manager_locations_views.Create.as_view(), name='new'),
    path(
        '<int:pk>/update/',
        manager_locations_views.Update.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_locations_views.Delete.as_view(),
        name='delete'
    ),
], 'locations')

manager_urlpatterns = ([
    path('', manager_core_views.Home.as_view(), name='home'),
    path('coach/', include(manager_coach_urlpatterns)),
    path('clients/', include(manager_clients_urlpatterns)),
    path('subscriptions/', include(manager_subscriptions_urlpatterns)),
    path('events/', include(manager_events_urlpatterns)),
    path('event-class/', include(manager_event_class_urlpatterns)),
    path('attendance/', include(manager_attendance_urlpatterns)),
    path('locations/', include(manager_locations_urlpatterns)),
    path('reports/', TemplateView.as_view(template_name='crm/manager/reports.html'),name='reports')
], 'manager')

urlpatterns = [
    path('', scrm_auth_views.SportCrmLoginRedirectView.as_view()),
    path('accounts/', include(auth_urlpatterns)),
    path('coach/', include(coach_urlpatterns)),
    path('manager/', include(manager_urlpatterns)),
]
