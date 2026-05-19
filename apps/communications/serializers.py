from rest_framework import serializers
from .models import MessageTemplate, MessageCampaign, WhatsAppGroup


class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTemplate
        fields = '__all__'


class MessageCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageCampaign
        fields = '__all__'


class WhatsAppGroupSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True, default='')
    region_name = serializers.CharField(source='region.name', read_only=True, default='')

    class Meta:
        model = WhatsAppGroup
        fields = '__all__'
