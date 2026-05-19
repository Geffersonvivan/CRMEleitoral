from django.db import models
from apps.core.models import TimeStampedModel


class MessageTemplate(TimeStampedModel):
    class Channel(models.TextChoices):
        WHATSAPP = 'whatsapp', 'WhatsApp'
        SMS = 'sms', 'SMS'
        EMAIL = 'email', 'E-mail'

    name = models.CharField('Nome', max_length=255)
    content = models.TextField('Conteúdo')
    channel = models.CharField('Canal', max_length=20, choices=Channel.choices)
    variables = models.JSONField('Variáveis', default=list, blank=True)

    class Meta:
        verbose_name = 'Template de Mensagem'
        verbose_name_plural = 'Templates de Mensagens'

    def __str__(self):
        return f'{self.name} ({self.get_channel_display()})'


class MessageCampaign(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Rascunho'
        SCHEDULED = 'scheduled', 'Agendada'
        SENDING = 'sending', 'Enviando'
        SENT = 'sent', 'Enviada'
        CANCELLED = 'cancelled', 'Cancelada'

    name = models.CharField('Nome', max_length=255)
    template = models.ForeignKey(
        MessageTemplate, verbose_name='Template',
        on_delete=models.SET_NULL, null=True
    )
    channel = models.CharField('Canal', max_length=20, choices=MessageTemplate.Channel.choices)
    target_contacts = models.ManyToManyField(
        'contacts.Contact', verbose_name='Contatos alvo', blank=True
    )
    target_filter = models.JSONField('Filtro de contatos', default=dict, blank=True)
    scheduled_at = models.DateTimeField('Agendado para', null=True, blank=True)
    sent_at = models.DateTimeField('Enviado em', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_sent = models.IntegerField('Total enviados', default=0)
    total_delivered = models.IntegerField('Total entregues', default=0)
    total_read = models.IntegerField('Total lidos', default=0)
    total_replied = models.IntegerField('Total respondidos', default=0)

    class Meta:
        verbose_name = 'Campanha de Mensagem'
        verbose_name_plural = 'Campanhas de Mensagens'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WhatsAppGroup(TimeStampedModel):
    class GroupType(models.TextChoices):
        COORDINATION = 'coordination', 'Coordenação'
        SUPPORTERS = 'supporters', 'Apoiadores'
        VOLUNTEERS = 'volunteers', 'Voluntários'
        CAMPAIGN = 'campaign', 'Campanha'

    name = models.CharField('Nome', max_length=255)
    group_type = models.CharField('Tipo', max_length=50, choices=GroupType.choices)
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    region = models.ForeignKey(
        'geography.Region', verbose_name='Região',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    member_count = models.IntegerField('Membros', default=0)
    admin_contact = models.ForeignKey(
        'contacts.Contact', verbose_name='Admin',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    invite_link = models.URLField('Link de convite', blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Grupo WhatsApp'
        verbose_name_plural = 'Grupos WhatsApp'
        ordering = ['name']

    def __str__(self):
        return self.name
