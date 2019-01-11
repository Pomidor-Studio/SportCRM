from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from .models import clients

# Create your views here.


def home(request):
    return render(request, 'crm/home.html')


def clientsv(request):
    context = {
        'clients': clients.objects.all()
    }
    return render(request, 'crm/clients.html', context)


class ClientsListView(ListView):
    model = clients
    template_name = 'crm/clients.html'
    context_object_name = 'clients'
    ordering = ['id']

class ClientDetailView(DetailView):
    model = clients
