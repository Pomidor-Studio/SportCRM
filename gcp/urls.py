from django.urls import path
from . import views

urlpatterns = [
     path('_ah/warmup', views.warm_up, name='warmup'),
]
