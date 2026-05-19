from django.contrib import admin
from .models import MessageTemplate, MessageCampaign, WhatsAppGroup


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel')
    list_filter = ('channel',)


@admin.register(MessageCampaign)
class MessageCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'status', 'scheduled_at', 'total_sent', 'total_delivered')
    list_filter = ('status', 'channel')


@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'group_type', 'city', 'region', 'member_count', 'is_active')
    list_filter = ('group_type', 'is_active', 'region')
    search_fields = ('name',)
