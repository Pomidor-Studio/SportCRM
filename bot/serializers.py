from rest_framework import serializers

from bot.models import MessageMeta


class MessageIgnoranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageMeta
        fields = ('is_enabled',)
