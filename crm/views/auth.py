from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    RedirectView, TemplateView, UpdateView,
)

from crm.forms import ProfileUserForm


class SportCrmLoginRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            return reverse('crm:accounts:login')
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
        return super().get(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'crm/auth/profile.html'
    form_class = ProfileUserForm
    success_url = reverse_lazy('crm:accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user
