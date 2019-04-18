from django.urls import path, include

from crm.views.manager.event_class import ApiCalendar
from crm.views.manager import event as manager_event_views
from crm.views.manager import subscription as manager_subscription_views
from crm.views import coach as coach_views


manager_event_class_urls = ([
    path('<int:pk>/calendar/', ApiCalendar.as_view(), name='calendar'),
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

urlpatterns = [
    path('manager/', include(manager_api_urls)),
    path('coach/', include(coach_api_urls)),
]
