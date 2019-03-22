from django.db import models

from crm.models import CompanyObjectModel


class MessageMeta(CompanyObjectModel):
    uuid = models.UUIDField('Код сообщения')
    is_enabled = models.BooleanField(
        'Включена ли отправка сообщения',
        default=True
    )
    template = models.TextField('Шаблон сообщения', max_length=10000)

    class Meta:
        unique_together = ['company', 'uuid']
