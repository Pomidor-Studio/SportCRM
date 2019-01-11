from django.urls import path
from .views import ClientsListView, ClientDetailView
from . import views

urlpatterns = [
    path('', views.home, name='crm-home'),
    path('clients/', ClientsListView.as_view(), name='crm-clients'),
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='crm-client-detail')
]
