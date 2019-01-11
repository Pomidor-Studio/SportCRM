from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from .models import Client

# Create your views here.


def home(request):
    return render(request, 'crm/home.html')


def clientsv(request):
    context = {
        'clients': Client.objects.all()
    }
    return render(request, 'crm/clients.html', context)


class ClientsListView(ListView):
    model = Client
    template_name = 'crm/clients.html'
    context_object_name = 'clients'
    ordering = ['id']

class ClientDetailView(DetailView):
    model = Client
