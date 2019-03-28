from django.core.exceptions import ValidationError

from bot.api.messages.base import Message
from bot.models import MessageMeta
from contrib.forms import TenantModelForm


class MessageTemplateEditForm(TenantModelForm):
    class Meta:
        model = MessageMeta
        fields = ('template',)

    def clean_template(self):
        if hasattr(self, 'msg_type') and issubclass(self.msg_type, Message):
            try:
                self.msg_type.prepare_raw_template(
                    self.cleaned_data['template']
                )
            except Exception as e:
                raise ValidationError(e, code='invalid')

        return self.cleaned_data['template']
