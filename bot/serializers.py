from rest_framework import serializers

from bot.models import MessageIgnorance


class MessageIgnoranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIgnorance
        fields = ('is_enabled',)
