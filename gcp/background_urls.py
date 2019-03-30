from django.urls import path
from django.urls import include
from . import views

urlpatterns = [
    path('google_task_handler/', views.google_task_handler, name='google-task-handler'),
    path('', include('gcp.urls')),
]



