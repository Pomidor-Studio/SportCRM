from django.db import models

from crm.models import CompanyObjectModel


class MessageIgnorance(CompanyObjectModel):
    type = models.CharField('Тип сообщения', max_length=250)
    is_enabled = models.BooleanField(
        'Включена ли отправка сообщения',
        default=True
    )

    class Meta:
        unique_together = ['id', 'company', 'type']
