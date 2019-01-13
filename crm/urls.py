from django.urls import path
from . import views


app_name = 'crm'
urlpatterns = [
    path('', views.home, name='crm-home'),
    path('clients/', views.ClientsListView.as_view(), name='clients'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='crm-client-detail'),
    path('eventclass/', views.EventClassList.as_view(), name='eventclass_list'),
    path('eventclass/create/', views.EventClassCreate.as_view(), name='eventclass_create'),
    path('eventclass/<int:pk>/update/', views.EventClassUpdate.as_view(), name='eventclass_update'),
    path('eventclass/<int:pk>/delete/', views.EventClassDelete.as_view(), name='eventclass_delete'),

]
