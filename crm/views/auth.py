from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    RedirectView, TemplateView, UpdateView,
)

from crm.forms import ProfileCoachForm, ProfileManagerForm


class SportCrmLoginRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            return reverse('crm:accounts:login')
        elif self.request.user.is_superuser:
            return reverse('admin:index')
        elif self.request.user.is_coach:
            return reverse('crm:coach:home')
        elif self.request.user.is_manager:
            return reverse('crm:manager:home')
        else:
            return reverse('crm:accounts:login')


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
        if request.session['confirm-reset']:
            self.password = get_user_model().objects.make_random_password()
            request.user.set_password(self.password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            ret = super().get(request, *args, **kwargs)
        else:
            ret = HttpResponseRedirect(reverse('crm:accounts:profile'))

        request.session['confirm-reset'] = False
        return ret


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'crm/auth/profile.html'
    success_url = reverse_lazy('crm:accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

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

    def get(self, request, *args, **kwargs):
        request.session['confirm-reset'] = False

        return super().get(request, *args, **kwargs)
