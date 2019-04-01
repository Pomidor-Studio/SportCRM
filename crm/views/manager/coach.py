import sesame.utils
import vk
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, UpdateView,
)
from django_filters.views import FilterView
from reversion.views import RevisionMixin
from rules.contrib.views import PermissionRequiredMixin
from social_django.utils import load_strategy, load_backend

from crm.filters import CoachFilter
from crm.forms import CoachMultiForm
from crm.models import Coach
from crm.utils import VK_PAGE_REGEXP
from crm.views.mixin import UnDeleteView, CreateAndAddMixin


class List(PermissionRequiredMixin, FilterView):
    model = Coach
    template_name = 'crm/manager/coach/list.html'
    context_object_name = 'coachs'
    paginate_by = 25
    filterset_class = CoachFilter
    permission_required = 'coach'


class Detail(PermissionRequiredMixin, DetailView):
    template_name = 'crm/manager/coach/detail.html'
    model = Coach
    context_object_name = 'coach'
    permission_required = 'coach.view_detail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_temp_link'] = '{host}{url}{qs}'.format(
            host=self.request.get_host(),
            url=reverse('crm:accounts:profile'),
            qs=sesame.utils.get_query_string(self.object.user)
        )
        return context


class SocialAuthMixin:
    provider = 'vk-oauth2'

    def get_vk_info(self, user_vk_link):
        match = VK_PAGE_REGEXP.match(user_vk_link)
        session = vk.Session()
        api = vk.API(session, v=5.90)

        try:
            return api.users.get(
                access_token=settings.VK_GROUP_TOKEN,
                user_ids=match.group('user_id')
            )[0]
        except (IndexError, AttributeError):
            return None

    def create_with_replace(self, user, vk_user):
        strategy = load_strategy(self.request)
        backend = load_backend(strategy, self.provider, '')

        linked_social = (
            backend.strategy.storage.user
            .get_social_auth_for_user(user, self.provider)
            .first()
        )

        if linked_social:
            # There was no edit of vk link, don't replace it
            if linked_social.uid == vk_user['id']:
                return

            linked_social.delete()

        try:
            backend.strategy.storage.user.create_social_auth(
                user, vk_user['id'], backend.name
            )
        except Exception as err:
            if not backend.strategy.storage.is_integrity_error(err):
                raise

    def set_social(self, user, user_vk_link):

        vk_user = self.get_vk_info(user_vk_link)
        if not vk_user:
            return

        self.create_with_replace(user, vk_user)


class Create(PermissionRequiredMixin, RevisionMixin, SocialAuthMixin, CreateAndAddMixin):
    template_name = 'crm/manager/coach/form.html'
    model = Coach
    form_class = CoachMultiForm
    permission_required = 'coach.add'
    add_another_url = 'crm:manager:coach:new'

    def form_valid(self, form):
        # User is generated manually as we need create
        # dynamic username for coach
        user = get_user_model().objects.create_coach(
            form['user']['first_name'].data,
            form['user']['last_name'].data
        )
        coach_form = form['coach']
        coach = coach_form.save(commit=False)
        coach.user = user
        coach.save()
        self.object = coach

        if coach_form.cleaned_data['vk_page']:
            self.set_social(user, coach_form.cleaned_data['vk_page'])

        return redirect(self.get_success_url())


class Update(
    PermissionRequiredMixin,
    RevisionMixin,
    SocialAuthMixin,
    UpdateView
):
    template_name = 'crm/manager/coach/form.html'
    model = Coach
    form_class = CoachMultiForm
    permission_required = 'coach.edit'

    def get_initial(self):
        initial = super().get_initial()
        # Multiform waits initials in subdictionary
        initial['coach'] = {'vk_page': self.object.user.vk_link}
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
        self.object = objects['coach']

        user = objects['user']
        coach_form = form['coach']
        if coach_form.cleaned_data['vk_page']:
            self.set_social(user, coach_form.cleaned_data['vk_page'])

        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(instance={
            'user': self.object.user,
            'coach': self.object,
        })
        return kwargs


class Delete(PermissionRequiredMixin, RevisionMixin, DeleteView):
    template_name = 'crm/manager/coach/confirm_delete.html'
    model = Coach
    context_object_name = 'coach'
    success_url = reverse_lazy('crm:manager:coach:list')
    permission_required = 'coach.delete'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        if self.object.has_active_events:
            messages.error(
                self.request,
                f'Невозможно удалить тренера {self.object}\n'
                f'У этого тренера есть активные тренировки.'
            )
            return HttpResponseRedirect(success_url)

        coach_name = str(self.object)
        user = self.object.user
        self.object.delete()
        user.is_active = False
        user.save()

        messages.info(self.request, f'Тренер {coach_name} удален.')

        return HttpResponseRedirect(success_url)


class Undelete(
    PermissionRequiredMixin,
    RevisionMixin,
    UnDeleteView
):
    template_name = 'crm/manager/coach/confirm_undelete.html'
    model = Coach
    context_object_name = 'coach'
    success_url = reverse_lazy('crm:manager:coach:list')
    permission_required = 'coach.undelete'

    def undelete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        success_url = self.get_success_url()
        self.object.undelete()
        user.is_active = True
        user.save()
        messages.info(self.request, f'Тренер {self.object} возвращен.')
        return HttpResponseRedirect(success_url)
