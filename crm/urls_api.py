from django.urls import path, include

from crm.views.manager.event_class import ApiCalendar
from crm.views.manager import event as manager_event_views

manager_event_class_urls = ([
    path('<int:pk>/calendar/', ApiCalendar.as_view(), name='calendar'),
], 'event-class')

manager_event_urls = ([
    path('', manager_event_views.ApiCalendar.as_view(), name='calendar'),
], 'event')

manager_api_urls = ([
    path('event-class/', include(manager_event_class_urls)),
    path('event/', include(manager_event_urls)),
], 'manager')

urlpatterns = [
    path('manager/', include(manager_api_urls)),
]
