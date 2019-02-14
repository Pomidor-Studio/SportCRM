import sesame.utils
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView,
    DeleteView,
)

from crm.models import Coach
from crm.views.mixin import UserManagerMixin
from crm.forms import CoachMultiForm


class List(LoginRequiredMixin, UserManagerMixin, ListView):
    model = Coach
    template_name = 'crm/manager/coach/list.html'
    context_object_name = 'coachs'
    paginate_by = 25


class Detail(LoginRequiredMixin, UserManagerMixin, DetailView):
    template_name = 'crm/manager/coach/detail.html'
    model = Coach
    context_object_name = 'coach'


class Create(LoginRequiredMixin, UserManagerMixin, CreateView):
    template_name = 'crm/manager/coach/form.html'
    model = Coach
    form_class = CoachMultiForm

    def form_valid(self, form):
        # User is generated manually as we need create
        # dynamic username for coach
        user = get_user_model().objects.create_coach(
            form['user']['first_name'].data,
            form['user']['last_name'].data
        )
        # TODO: Return after coach extra field added to form
        # coach = form['coach'].save(commit=False)
        coach = Coach()
        coach.user = user
        coach.save()
        self.object = coach
        return redirect(self.get_success_url())


class Update(LoginRequiredMixin, UserManagerMixin, UpdateView):
    template_name = 'crm/manager/coach/form.html'
    model = Coach
    form_class = CoachMultiForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.object.user.has_vk_auth:
            context['login_temp_link'] = '{host}{url}{qs}'.format(
                host=self.request.get_host(),
                url=reverse('crm:coach:home'),
                qs=sesame.utils.get_query_string(self.object.user)
            )

        return context

    def form_valid(self, form):
        objects = form.save()
        self.object = objects['user'].coach
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(instance={
            'user': self.object.user,
            'coach': self.object,
        })
        return kwargs


class Delete(LoginRequiredMixin, UserManagerMixin, DeleteView):
    template_name = 'crm/manager/coach/delete.html'
    model = Coach
    context_object_name = 'coach'
    success_url = reverse_lazy('crm:manager:coach:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        success_url = self.get_success_url()
        self.object.delete()
        user.delete()
        return HttpResponseRedirect(success_url)

