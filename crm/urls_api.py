from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from crm.views.manager.event_class import ApiCalendar
from crm.views.manager import event as manager_event_views
from crm.views.manager import event_class as manager_event_class_views
from crm.views.manager import subscription as manager_subscription_views
from crm.views import (
    coach as coach_views,
    landing as landing_views,
)


manager_event_class_urls = ([
    path('<int:pk>/calendar/', ApiCalendar.as_view(), name='calendar'),
    path('', manager_event_class_views.CreateEventClass.as_view(), name='create'),
    path(
        '<int:pk>/',
        manager_event_class_views.UpdateEventClass.as_view(),
        name='update'
    )
], 'event-class')

manager_event_urls = ([
    path('', manager_event_views.ApiCalendar.as_view(), name='calendar'),
], 'event')

manager_subscription_urls = ([
    path(
        '<int:pk>/sell-range/',
        manager_subscription_views.SellRange.as_view(),
        name='sell-range'
    )
], 'subscription')

manager_api_urls = ([
    path('event-class/', include(manager_event_class_urls)),
    path('event/', include(manager_event_urls)),
    path('subscription/', include(manager_subscription_urls)),
], 'manager')

coach_api_urls = ([
    path('calendar/', coach_views.ApiCalendar.as_view(), name='calendar')
], 'coach')

landing_api_urls = (
    [
        path(
            'register/',
            landing_views.RegisterCompanyView.as_view(),
            name='register'
        )
    ], 'landing'
)


urlpatterns = [
    path('manager/', include(manager_api_urls)),
    path('coach/', include(coach_api_urls)),
    path('landing/', include(landing_api_urls)),
]
