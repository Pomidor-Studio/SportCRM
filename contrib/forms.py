from django import forms
from django_multitenant.utils import get_current_tenant


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


class TenantModelForm(TenantFormMixin, forms.ModelForm):
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


class TenantForm(TenantFormMixin, forms.Form):
    """
    Base class for non-model forms with multi-tenant support
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check form ChoiceFields
        self.filter_choice_queryset()
