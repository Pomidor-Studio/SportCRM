from bot.models import MessageMeta
from crm.forms import TenantModelForm


class MessageTemplateEditForm(TenantModelForm):
    class Meta:
        model = MessageMeta
        fields = ('template',)
