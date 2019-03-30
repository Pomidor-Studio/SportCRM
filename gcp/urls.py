from django.conf.urls import url
from . import views

urlpatterns = [
     url('_ah/warmup', views.warm_up, name='warmup'),
]
