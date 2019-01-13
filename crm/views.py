from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse, reverse_lazy

from .models import Client, EventClass


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


class EventClassList(ListView):
    # template_name = 'polls/index.html'
    # context_object_name = 'latest_question_list'
    model = EventClass


class EventClassCreate(CreateView):
    model = EventClass
    fields = '__all__'
    #fields = ['name']


class EventClassUpdate(UpdateView):
    model = EventClass
    fields = '__all__'

