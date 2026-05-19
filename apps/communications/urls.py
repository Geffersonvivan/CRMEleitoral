from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageTemplateViewSet, MessageCampaignViewSet, WhatsAppGroupViewSet

app_name = 'communications'

router = DefaultRouter()
router.register(r'templates', MessageTemplateViewSet, basename='template')
router.register(r'campaigns', MessageCampaignViewSet, basename='message-campaign')
router.register(r'whatsapp-groups', WhatsAppGroupViewSet, basename='whatsapp-group')

urlpatterns = [
    path('', include(router.urls)),
]
