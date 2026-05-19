from rest_framework import viewsets
from .models import MessageTemplate, MessageCampaign, WhatsAppGroup
from .serializers import MessageTemplateSerializer, MessageCampaignSerializer, WhatsAppGroupSerializer


class MessageTemplateViewSet(viewsets.ModelViewSet):
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    filterset_fields = ['channel']


class MessageCampaignViewSet(viewsets.ModelViewSet):
    queryset = MessageCampaign.objects.all()
    serializer_class = MessageCampaignSerializer
    filterset_fields = ['status', 'channel']


class WhatsAppGroupViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppGroup.objects.select_related('city', 'region').all()
    serializer_class = WhatsAppGroupSerializer
    filterset_fields = ['group_type', 'region', 'city', 'is_active']
