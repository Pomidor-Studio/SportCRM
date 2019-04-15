from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django_multitenant.utils import get_current_tenant, set_current_tenant


class TenantFormMixin:
    def filter_choice_queryset(self):
        """
        Class initialized ChoiceFields don't handle client tenant,
        so we must manually apply filter on such fields

        This function must be applied in __init__ and
        **after** super().__init__
        """
        tenant = get_current_tenant()
        if not tenant:
            return

        for field in self.fields.values():
            if isinstance(
                field,
                (forms.ModelChoiceField, forms.ModelMultipleChoiceField)
            ):
                # Check if the model being used for the ModelChoiceField
                # has a tenant model field
                if hasattr(field.queryset.model, 'tenant_id'):
                    # Add filter restricting queryset to values to this
                    # tenant only.
                    kwargs = {field.queryset.model.tenant_id: tenant}
                    field.queryset = field.queryset.filter(**kwargs)


class ArchivedFormMixin:
    def filter_archived_queryset(self):
        """
        Class initialized ChoiceFields don't handle models that are
        *safe deleted*, so we must manually apply filter on such fields

        This function must be applied in __init__ and
        **after** super().__init__
        """

        for field in self.fields.values():
            # Avoid circular import
            # TODO: move SafeDeleteModel and mixins to contrib app
            from safedelete.models import SafeDeleteModel
            if isinstance(
                field,
                (forms.ModelChoiceField, forms.ModelMultipleChoiceField)
            ) and issubclass(field.queryset.model, SafeDeleteModel):
                # Avoid archived data in queryset
                kwargs = {'deleted__isnull': True}
                field.queryset = field.queryset.filter(**kwargs)


class TenantModelForm(TenantFormMixin, ArchivedFormMixin, forms.ModelForm):
    """
    Base from for multitenant
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # "company" is application wide tenant name, so remove it from
        # class form. User don't need to see this value, as it is for
        # internal purposes
        if "company" in self.fields:
            del self.fields["company"]

        # Check form ChoiceFields
        self.filter_choice_queryset()
        self.filter_archived_queryset()


class TenantForm(TenantFormMixin, ArchivedFormMixin, forms.Form):
    """
    Base class for non-model forms with multi-tenant support
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check form ChoiceFields
        self.filter_choice_queryset()
        self.filter_archived_queryset()


class NonTenantUsernameMixin:
    """
    Validate username field with tenant ignorance, as username must be uniq
    across all tenants
    """
    def clean_username(self):
        username = self.cleaned_data['username']

        # Don't check username uniqueness if it wasn't changed
        if 'username' not in self.changed_data:
            return username

        current_tenant = get_current_tenant()
        set_current_tenant(None)
        if get_user_model().objects.filter(username=username).exists():
            set_current_tenant(current_tenant)
            raise ValidationError(
                _('User with name %(username)s exists'),
                code='invalid',
                params={'username': username}
            )

        set_current_tenant(current_tenant)
        return username
