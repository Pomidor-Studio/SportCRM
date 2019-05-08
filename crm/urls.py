from django.contrib.auth import views as auth_views
from django.urls import include, path

from crm.views import auth as scrm_auth_views, coach as coach_views
from crm.views.manager import (
    attendance as manager_attendance_views,
    balance as manager_balance_views,
    client as manager_client_views,
    coach as manager_coach_views,
    core as manager_core_views,
    event as manager_event_views,
    event_class as manager_event_class_views,
    location as manager_locations_views,
    manager as manager_manager_views,
    report as manager_report_views,
    subscription as manager_subs_views,
    company as manager_company_views,
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

manager_manager_urlpatterns = ([
    path('', manager_manager_views.List.as_view(), name='list'),
    path('<int:pk>/', manager_manager_views.Detail.as_view(), name='detail'),
    path('new/', manager_manager_views.Create.as_view(), name='new'),
    path(
        '<int:pk>/update/',
        manager_manager_views.Update.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/delete/',
        manager_manager_views.Delete.as_view(),
        name='delete'
    ),
    path(
        '<int:pk>/undelete/',
        manager_manager_views.Undelete.as_view(),
        name='undelete'
    )
], 'manager')

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

manager_client_balance_urlpatterns = ([
    path('', manager_balance_views.Create.as_view(), name='new')
], 'balance')

manager_clients_urlpatterns = ([
    path('', manager_client_views.List.as_view(), name='list'),
    path('<int:pk>/', manager_client_views.Detail.as_view(), name='detail'),
    path('<int:pk>/balance/', include(manager_client_balance_urlpatterns)),
    path('new/', manager_client_views.Create.as_view(), name='new'),
    path('import-report/', manager_client_views.ImportReport.as_view(), name='import-report'),
    path('upload-excel/', manager_client_views.UploadExcel.as_view(), name='excel'),
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
        '<int:pk>/undelete/',
        manager_client_views.UnDelete.as_view(),
        name='undelete'
    ),
    path(
        '<int:client_id>/add-subscription/',
        manager_client_views.AddSubscription.as_view(),
        name='new-subscription'
    ),
    path(
        '<int:client_id>/add-subscription-with-extending',
        manager_client_views.AddSubscriptionWithExtending.as_view(),
        name='add-subscription-with-extending'
    ),
    path(
        'subscription/',
        include(manager_client_subs_urlpatterns)
    ),
    path(
        'check-overlapping/',
        manager_client_views.CheckOverlapping.as_view(),
        name='check-overlapping'
    ),
    path(
        'unmark/<int:event_class_id>/<int:year>/<int:month>/<int:day>/<int:client_id>',
        manager_client_views.UnMarkClient.as_view(),
        name='unmark-client'
    ),
    path(
        'cancel-att/<int:event_class_id>/<int:year>/<int:month>/<int:day>/<int:client_id>',
        manager_client_views.CancelAttendance.as_view(),
        name='cancel-att'
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

manager_events_urlpatterns = ([
    path('', manager_event_views.Calendar.as_view(), name='calendar'),
    path(
        'report/event/',
        manager_event_views.EventReport.as_view(),
        name='event-report'
    ),
    path(
       'report/visit/',
       manager_event_views.VisitReport.as_view(),
       name='visit-report'
    ),
], 'event')

manager_event_urlpatterns = ([
    path(
        '',
        manager_event_class_views.EventByDate.as_view(),
        name='event-by-date'
    ),
    path(
        'mark/<int:client_id>/<int:subscription_id>',
        manager_event_class_views.MarkClient.as_view(),
        name='mark-client'
    ),
    path(
        'mark-without-subscription',
        manager_event_class_views.SignUpClientWithoutSubscription.as_view(),
        name='mark-client-without-subscription'
    ),
    path(
        'unmark/<int:client_id>',
        manager_event_class_views.UnMarkClient.as_view(),
        name='unmark-client'
    ),
    path(
        'sign-up/<int:client_id>',
        manager_event_class_views.SignUpClient.as_view(),
        name='sign-up-client'
    ),
    path(
        'sell-and-mark/',
        manager_event_class_views.SellAndMark.as_view(),
        name='sell-and-mark'
    ),
    path(
        'sell-and-mark/<int:client_id>',
        manager_event_class_views.SellAndMark.as_view(),
        name='sell-and-mark-to-client'
    ),
    path(
        'cancel-att/<int:client_id>',
        manager_event_class_views.CancelAttendance.as_view(),
        name='cancel-att'
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
        'close/',
        manager_event_class_views.DoCloseEvent.as_view(),
        name='close'
    ),
    path(
        'open/',
        manager_event_class_views.DoOpenEvent.as_view(),
        name='open'
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
        manager_locations_views.List.as_view(),
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
    path(
        '<int:pk>/undelete/',
        manager_locations_views.Undelete.as_view(),
        name='undelete'
    )
], 'locations')

manager_urlpatterns = ([
    path('', manager_core_views.Home.as_view(), name='home'),
    path('company/', manager_company_views.Edit.as_view(), name='company'),
    path('coach/', include(manager_coach_urlpatterns)),
    path('manager/', include(manager_manager_urlpatterns)),
    path('clients/', include(manager_clients_urlpatterns)),
    path('subscriptions/', include(manager_subscriptions_urlpatterns)),
    path('events/', include(manager_events_urlpatterns)),
    path('event-class/', include(manager_event_class_urlpatterns)),
    path('attendance/', include(manager_attendance_urlpatterns)),
    path('locations/', include(manager_locations_urlpatterns)),
    path(
        'reports/',
        manager_report_views.ReportList.as_view(),
        name='reports'
    )
], 'manager')

urlpatterns = [
    path('', scrm_auth_views.SportCrmLoginRedirectView.as_view()),
    path('accounts/', include(auth_urlpatterns)),
    path('coach/', include(coach_urlpatterns)),
    path('manager/', include(manager_urlpatterns)),
]
