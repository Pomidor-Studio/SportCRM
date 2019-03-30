from django.conf.urls import url
from django.urls import include
from . import views

urlpatterns = [
    url('google_task_handler/', views.google_task_handler, name='google-task-handler'),
    include('gcp.urls')
]



