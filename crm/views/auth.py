from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordContextMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import (
    FormView, RedirectView, TemplateView, UpdateView,
)

from crm.forms import ProfileCoachForm, ProfileManagerForm
from crm.views.mixin import SocialAuthMixin


class SportCrmLoginRedirectView(TemplateView):
    template_name = 'crm/landing.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        redirect_url = self.get_redirect_url()

        if redirect_url:
            return HttpResponseRedirect(redirect_url)

        return self.render_to_response(context)

    def get_redirect_url(self):
        if self.request.user.is_anonymous:
            return None
        elif self.request.user.is_superuser:
            return reverse('admin:index')
        elif self.request.user.is_coach:
            return reverse('crm:coach:home')
        elif self.request.user.is_manager:
            return reverse('crm:manager:event:calendar')
        else:
            return None


class SportCrmPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('crm:accounts:profile')
    template_name = 'crm/auth/password-change.html'


class ResetPasswordConfirmView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/auth/password-reset-confirm.html'

    def get(self, request, *args, **kwargs):
        request.session['confirm-reset'] = True
        return super().get(request, *args, **kwargs)


class ResetPasswordView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/auth/password-reset.html'
    password: str = ...

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password'] = self.password
        return context

    def get(self, request, *args, **kwargs):
        self.password = get_user_model().objects.make_random_password()
        request.user.set_password(self.password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        return super().get(request, *args, **kwargs)


class SetPasswordView(PasswordContextMixin, FormView):
    form_class = SetPasswordForm
    template_name = 'crm/auth/first-login.html'
    title = 'Установка пароля'

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.request.user.has_usable_password():
            return HttpResponseRedirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse('admin:index')
        elif self.request.user.is_coach:
            return reverse('crm:coach:home')
        elif self.request.user.is_manager:
            return reverse('crm:manager:event:calendar')
        else:
            return reverse('crm:accounts:login')

class ProfileView(LoginRequiredMixin, SocialAuthMixin, UpdateView):
    template_name = 'crm/auth/profile.html'
    success_url = reverse_lazy('crm:accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_initial(self):
        initial = super().get_initial()
        # Multiform waits initials in subdictionary
        initial['detail'] = {'vk_page': self.object.vk_link}
        return initial

    def get_form_class(self):
        if self.request.user.is_manager:
            return ProfileManagerForm
        else:
            return ProfileCoachForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(instance={
            'user': self.object,
            'detail':
                self.object.manager
                if self.object.is_manager
                else self.object.coach,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context_date = super().get_context_data(**kwargs)
        context_date['next'] = self.get_success_url()
        return context_date

    def get(self, request, *args, **kwargs):
        request.session['confirm-reset'] = False

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if form['detail'].cleaned_data['vk_page']:
            self.set_social(
                self.request.user, form['detail'].cleaned_data['vk_page'])
        elif self.request.user.vk_id is not None:
            self.delete_social(self.request.user)

        return response


