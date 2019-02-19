from django.urls import path, include

from crm.views.manager.event_class import ApiCalendar

manager_event_class_urls = ([
    path('<int:pk>/calendar/', ApiCalendar.as_view(), name='calendar'),
], 'event-class')

manager_api_urls = ([
    path('event-class/', include(manager_event_class_urls)),
], 'manager')

urlpatterns = [
    path('manager/', include(manager_api_urls)),
]
