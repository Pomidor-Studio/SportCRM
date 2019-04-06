from rest_framework import serializers


class VkSerializer(serializers.Serializer):
    vkId = serializers.IntegerField(write_only=True)
    vkGroup = serializers.IntegerField(write_only=True)


class VkActionSerializer(VkSerializer):
    year = serializers.IntegerField(write_only=True)
    month = serializers.IntegerField(write_only=True)
    day = serializers.IntegerField(write_only=True)
    eventClassId = serializers.IntegerField(write_only=True)


class VkAdminOptionsSerializer(VkSerializer):
    accessToken = serializers.CharField(write_only=True)
    botConfirm = serializers.CharField(write_only=True)
