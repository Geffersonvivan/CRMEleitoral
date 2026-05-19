from django.db import models
from apps.core.models import TimeStampedModel, AddressMixin


class Tag(models.Model):
    name = models.CharField('Nome', max_length=50, unique=True)
    color = models.CharField('Cor', max_length=7, default='#6c757d')

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def __str__(self):
        return self.name


class Contact(TimeStampedModel, AddressMixin):
    class Category(models.TextChoices):
        COORD_REGIONAL = 'coordenador_regional', 'Coordenador Regional'
        COORD_MUNICIPAL = 'coordenador_municipal', 'Coordenador Municipal'
        COORD_BAIRRO = 'coordenador_bairro', 'Coordenador de Bairro'
        APOIADOR = 'apoiador', 'Apoiador'
        PARCEIRO = 'parceiro', 'Parceiro'
        LIDERANCA = 'lideranca', 'Liderança Comunitária'
        VEREADOR = 'vereador', 'Vereador'
        PREFEITO = 'prefeito', 'Prefeito'
        DEPUTADO = 'deputado', 'Deputado'
        ELEITOR = 'eleitor', 'Eleitor'
        INDECISO = 'indeciso', 'Indeciso'
        OPOSICAO = 'oposicao', 'Oposição'

    class EngagementLevel(models.IntegerChoices):
        COLD = 1, 'Frio - Sem contato'
        WARM = 2, 'Morno - Primeiro contato'
        HOT = 3, 'Quente - Engajado'
        VERY_HOT = 4, 'Muito Quente - Ativo na campanha'
        AMBASSADOR = 5, 'Embaixador - Multiplica votos'

    full_name = models.CharField('Nome completo', max_length=255)
    nickname = models.CharField('Apelido', max_length=100, blank=True)
    cpf = models.CharField('CPF', max_length=14, blank=True, unique=True, null=True)
    email = models.EmailField('E-mail', blank=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True)
    category = models.CharField(
        'Categoria', max_length=30,
        choices=Category.choices, default=Category.ELEITOR, db_index=True
    )
    engagement_level = models.IntegerField(
        'Nível de engajamento',
        choices=EngagementLevel.choices, default=EngagementLevel.COLD, db_index=True
    )
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts'
    )
    region = models.ForeignKey(
        'geography.Region', verbose_name='Região',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts'
    )
    neighborhood = models.ForeignKey(
        'geography.Neighborhood', verbose_name='Bairro',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts'
    )
    birth_date = models.DateField('Data de nascimento', null=True, blank=True)
    profession = models.CharField('Profissão', max_length=200, blank=True)
    party = models.CharField('Partido', max_length=50, blank=True)
    voter_registration = models.CharField('Título de eleitor', max_length=20, blank=True)
    electoral_zone = models.CharField('Zona eleitoral', max_length=10, blank=True)
    electoral_section = models.CharField('Seção eleitoral', max_length=10, blank=True)
    photo = models.ImageField('Foto', upload_to='contacts/photos/', blank=True)
    notes = models.TextField('Observações', blank=True)
    tags = models.ManyToManyField(Tag, verbose_name='Tags', blank=True)
    referred_by = models.ForeignKey(
        'self', verbose_name='Indicado por',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals'
    )
    is_active = models.BooleanField('Ativo', default=True, db_index=True)

    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if self.city and not self.region:
            self.region = self.city.region
        super().save(*args, **kwargs)


class CompanyPartner(TimeStampedModel, AddressMixin):
    name = models.CharField('Nome', max_length=255)
    cnpj = models.CharField('CNPJ', max_length=18, blank=True)
    contact_person = models.ForeignKey(
        Contact, verbose_name='Pessoa de contato',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='companies'
    )
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    sector = models.CharField('Setor', max_length=100, blank=True)
    employees_count = models.IntegerField('Funcionários', default=0)
    partnership_type = models.CharField('Tipo de parceria', max_length=100, blank=True)
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Empresa Parceira'
        verbose_name_plural = 'Empresas Parceiras'
        ordering = ['name']

    def __str__(self):
        return self.name


class Interaction(TimeStampedModel):
    class InteractionType(models.TextChoices):
        PHONE = 'phone_call', 'Ligação'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        MEETING = 'meeting', 'Reunião'
        EVENT = 'event', 'Evento'
        DOOR_TO_DOOR = 'door_to_door', 'Porta a Porta'
        SOCIAL_MEDIA = 'social_media', 'Rede Social'
        EMAIL = 'email', 'E-mail'
        REFERRAL = 'referral', 'Indicação'

    contact = models.ForeignKey(
        Contact, verbose_name='Contato',
        on_delete=models.CASCADE, related_name='interactions'
    )
    interaction_type = models.CharField(
        'Tipo', max_length=20, choices=InteractionType.choices
    )
    description = models.TextField('Descrição', blank=True)
    performed_by = models.ForeignKey(
        'accounts.User', verbose_name='Realizado por',
        on_delete=models.SET_NULL, null=True
    )
    outcome = models.CharField('Resultado', max_length=255, blank=True)
    next_action = models.CharField('Próxima ação', max_length=255, blank=True)
    next_action_date = models.DateField('Data próxima ação', null=True, blank=True)

    class Meta:
        verbose_name = 'Interação'
        verbose_name_plural = 'Interações'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_interaction_type_display()} - {self.contact}'
