from rest_framework import serializers


class VkActionSerializer(serializers.Serializer):
    vkId = serializers.IntegerField(write_only=True)
    vkGroup = serializers.IntegerField(write_only=True)
    year = serializers.IntegerField(write_only=True)
    month = serializers.IntegerField(write_only=True)
    day = serializers.IntegerField(write_only=True)
    eventClassId = serializers.IntegerField(write_only=True)
    success = serializers.BooleanField(read_only=True)


