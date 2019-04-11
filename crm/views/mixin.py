from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, RedirectView
from django.views.generic.detail import (
    BaseDetailView,
    SingleObjectTemplateResponseMixin,
)
from social_django.utils import load_backend, load_strategy

from contrib.vk_utils import get_one_vk_user_info, get_vk_id_from_link


class CreateAndAddView(CreateView):
    message_info = 'Объект создан'
    add_another_url = 'crm:manager:home'

    def post(self, request, *args, **kwargs):
        saved = super().post(request, *args, **kwargs)
        if "another" in request.POST:
            messages.info(request, self.message_info)
            return HttpResponseRedirect(reverse(self.add_another_url))
        else:
            return saved


class SocialAuthMixin:
    provider = 'vk-oauth2'

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
        vk_id = get_vk_id_from_link(user_vk_link)
        if not vk_id:
            return

        vk_user = get_one_vk_user_info(vk_id)

        if not vk_user:
            return

        self.create_with_replace(user, vk_user)


class UnDeletionMixin:
    """Provide the ability to undelete objects."""
    # TODO: on initialization add validation of object class
    #  to have undelete method
    success_url = None

    def undelete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        if hasattr(self.object, 'undelete'):
            self.object.undelete()
        return HttpResponseRedirect(success_url)

    def get_queryset(self):
        if self.queryset is None:
            if self.model:
                return self.model.all_objects.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.queryset.all()

    # Add support for browsers which only accept GET and POST for now.
    def post(self, request, *args, **kwargs):
        return self.undelete(request, *args, **kwargs)

    def get_success_url(self):
        if self.success_url:
            return self.success_url.format(**self.object.__dict__)
        else:
            raise ImproperlyConfigured(
                "No URL to redirect to. Provide a success_url.")


class BaseUnDeleteView(UnDeletionMixin, BaseDetailView):
    """
    Base view for undeleting an object.

    Using this base class requires subclassing to provide a response mixin.
    """


class UnDeleteView(SingleObjectTemplateResponseMixin, BaseUnDeleteView):
    """
    View for undeleting an object retrieved with self.get_object(), with a
    response rendered by a template.
    """
    template_name_suffix = '_confirm_undelete'


class RedirectWithActionView(RedirectView):
    def run_action(self):
        pass

    def get(self, request, *args, **kwargs):
        self.run_action()

        return super().get(request, *args, **kwargs)
