import sesame.utils
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (DeleteView, DetailView, ListView, UpdateView)
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin

from crm.forms import ManagerMultiForm
from crm.models import Manager
from crm.views.mixin import CreateAndAddView, SocialAuthMixin


class List(PermissionRequiredMixin, ListView):
    model = Manager
    template_name = 'crm/manager/manager/list.html'
    context_object_name = 'managers'
    paginate_by = 25
    permission_required = 'manager'


class Detail(PermissionRequiredMixin, DetailView):
    template_name = 'crm/manager/manager/detail.html'
    model = Manager
    context_object_name = 'manager'
    permission_required = 'manager.view_detail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_temp_link'] = '{host}{url}{qs}'.format(
            host=self.request.get_host(),
            url=reverse('crm:accounts:profile'),
            qs=sesame.utils.get_query_string(self.object.user)
        )
        return context

class Create(
    PermissionRequiredMixin,
    RevisionMixin,
    SocialAuthMixin,
    CreateAndAddView
):
    template_name = 'crm/manager/manager/form.html'
    model = Manager
    form_class = ManagerMultiForm
    permission_required = 'manager.add'
    add_another_url = 'crm:manager:manager:new'
    message_info = 'Менеджер успешно создан'

    def form_valid(self, form):
        # User is generated manually as we need create
        # dynamic username for coach
        user = get_user_model().objects.create_coach(
            form['user']['first_name'].data,
            form['user']['last_name'].data
        )
        manager_form = form['manager']
        manager = manager_form.save(commit=False)
        manager.user = user
        manager.save()
        self.object = manager

        if manager_form.cleaned_data['vk_page']:
            self.set_social(user, manager_form.cleaned_data['vk_page'])

        return redirect(self.get_success_url())


class Update(
    PermissionRequiredMixin,
    RevisionMixin,
    SocialAuthMixin,
    UpdateView
):
    template_name = 'crm/manager/manager/form.html'
    model = Manager
    form_class = ManagerMultiForm
    permission_required = 'manager.edit'

    def get_initial(self):
        initial = super().get_initial()
        # Multiform waits initials in subdictionary
        initial['manager'] = {'vk_page': self.object.user.vk_link}
        return initial

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
        self.object = objects['manager']

        user = objects['user']
        manager_form = form['manager']
        if manager_form.cleaned_data['vk_page']:
            self.set_social(user, manager_form.cleaned_data['vk_page'])

        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(instance={
            'user': self.object.user,
            'manager': self.object,
        })
        return kwargs


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    template_name = 'crm/manager/manager/confirm_delete.html'
    model = Manager
    context_object_name = 'manager'
    success_url = reverse_lazy('crm:manager:manager:list')
    permission_required = 'manager.delete'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        manager_name = str(self.object)
        user = self.object.user
        self.object.delete()
        user.is_active = False
        user.save()

        messages.info(self.request, f'Менеджер {manager_name} удален.')

        return HttpResponseRedirect(success_url)
