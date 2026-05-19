from django.db import models
from apps.core.models import TimeStampedModel


class Campaign(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planejada'
        ACTIVE = 'active', 'Ativa'
        PAUSED = 'paused', 'Pausada'
        COMPLETED = 'completed', 'Concluída'

    name = models.CharField('Nome', max_length=255)
    description = models.TextField('Descrição', blank=True)
    start_date = models.DateField('Data início')
    end_date = models.DateField('Data fim', null=True, blank=True)
    target_regions = models.ManyToManyField(
        'geography.Region', verbose_name='Regiões alvo', blank=True
    )
    target_cities = models.ManyToManyField(
        'geography.City', verbose_name='Cidades alvo', blank=True
    )
    responsible = models.ForeignKey(
        'accounts.User', verbose_name='Responsável',
        on_delete=models.SET_NULL, null=True
    )
    status = models.CharField('Status', max_length=20, choices=Status.choices, default=Status.PLANNED)
    goal_contacts = models.IntegerField('Meta de contatos', default=0)
    achieved_contacts = models.IntegerField('Contatos realizados', default=0)

    class Meta:
        verbose_name = 'Campanha'
        verbose_name_plural = 'Campanhas'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def progress_percentage(self):
        if self.goal_contacts == 0:
            return 0
        return round((self.achieved_contacts / self.goal_contacts) * 100, 2)


class Task(TimeStampedModel):
    class Phase(models.TextChoices):
        PLANNED = 'planned', 'Planejada'
        ARTICULATING = 'articulating', 'Em Articulação'
        SCHEDULED = 'scheduled', 'Agendada'
        EXECUTED = 'executed', 'Executada'
        COMPLETED = 'completed', 'Concluída'

    class TaskType(models.TextChoices):
        MEETING = 'meeting', 'Reunião com liderança'
        EVENT = 'event', 'Evento presencial'
        FIELD_VISIT = 'field_visit', 'Visita de campo'
        PARTY_WORK = 'party_work', 'Articulação partidária'
        COMMUNICATION = 'communication', 'Ação de comunicação'
        RECRUITMENT = 'recruitment', 'Captação de apoiador'

    class Priority(models.TextChoices):
        LOW = 'low', 'Baixa'
        MEDIUM = 'medium', 'Média'
        HIGH = 'high', 'Alta'
        URGENT = 'urgent', 'Urgente'

    campaign = models.ForeignKey(
        Campaign, verbose_name='Campanha',
        on_delete=models.CASCADE, related_name='tasks',
        null=True, blank=True,
    )
    title = models.CharField('Título', max_length=255)
    description = models.TextField('Descrição', blank=True)
    task_type = models.CharField(
        'Tipo', max_length=20,
        choices=TaskType.choices, default=TaskType.FIELD_VISIT,
    )
    phase = models.CharField(
        'Fase', max_length=20,
        choices=Phase.choices, default=Phase.PLANNED, db_index=True,
    )
    priority = models.CharField(
        'Prioridade', max_length=10,
        choices=Priority.choices, default=Priority.MEDIUM,
    )
    assigned_to = models.ForeignKey(
        'accounts.User', verbose_name='Atribuído a',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks',
    )
    due_date = models.DateField('Prazo', null=True, blank=True)
    completed_at = models.DateField('Concluida em', null=True, blank=True)
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tasks',
    )
    region = models.ForeignKey(
        'geography.Region', verbose_name='Região',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tasks',
    )
    goal_description = models.CharField(
        'Meta da demanda', max_length=255, blank=True,
        help_text='Ex: conquistar 50 apoiadores',
    )
    goal_achieved = models.IntegerField('Resultado obtido', default=0)

    class Meta:
        verbose_name = 'Demanda'
        verbose_name_plural = 'Demandas'
        ordering = ['-priority', 'due_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Preencher regiao automaticamente a partir da cidade
        if self.city and not self.region:
            self.region = self.city.region
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_date and self.phase != self.Phase.COMPLETED:
            from datetime import date
            return self.due_date < date.today()
        return False


class Itinerary(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planejado'
        CONFIRMED = 'confirmed', 'Confirmado'
        IN_PROGRESS = 'in_progress', 'Em Andamento'
        COMPLETED = 'completed', 'Concluído'

    name = models.CharField('Nome', max_length=255)
    start_date = models.DateField('Data início')
    end_date = models.DateField('Data fim')
    responsible = models.ForeignKey(
        'accounts.User', verbose_name='Responsável',
        on_delete=models.SET_NULL, null=True, blank=True,
    )
    target_regions = models.ManyToManyField(
        'geography.Region', verbose_name='Regiões', blank=True,
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=Status.choices, default=Status.PLANNED,
    )
    origin_city = models.ForeignKey(
        'geography.City', verbose_name='Cidade de saída',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='itineraries_origin',
        help_text='Cidade de onde o candidato parte',
    )
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Roteiro'
        verbose_name_plural = 'Roteiros'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class ItineraryStop(TimeStampedModel):
    itinerary = models.ForeignKey(
        Itinerary, verbose_name='Roteiro',
        on_delete=models.CASCADE, related_name='stops',
    )
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task, verbose_name='Demanda',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='itinerary_stops',
    )
    date = models.DateField('Data')
    scheduled_time = models.TimeField('Hora prevista', null=True, blank=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    travel_minutes = models.PositiveIntegerField('Deslocamento (min)', default=0,
        help_text='Tempo até a próxima parada',
    )
    is_overnight = models.BooleanField('Pernoite', default=False)
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Parada'
        verbose_name_plural = 'Paradas'
        ordering = ['date', 'order']

    def __str__(self):
        return f'{self.city.name} - {self.date}'


class Content(TimeStampedModel):
    class ContentType(models.TextChoices):
        BRIEFING = 'briefing', 'Briefing'
        SOCIAL_POST = 'social_post', 'Post redes sociais'
        WHATSAPP = 'whatsapp', 'Material WhatsApp'
        PHOTO = 'photo', 'Registro fotográfico'
        VIDEO = 'video', 'Vídeo'
        PRESS = 'press', 'Nota de imprensa'

    class Phase(models.TextChoices):
        BEFORE = 'before', 'Antes da ação'
        AFTER = 'after', 'Depois da ação'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        IN_PRODUCTION = 'in_production', 'Em produção'
        APPROVED = 'approved', 'Aprovado'
        PUBLISHED = 'published', 'Publicado'

    task = models.ForeignKey(
        Task, verbose_name='Demanda',
        on_delete=models.CASCADE, related_name='contents',
    )
    content_type = models.CharField(
        'Tipo', max_length=20, choices=ContentType.choices,
    )
    phase = models.CharField(
        'Fase', max_length=10, choices=Phase.choices,
    )
    title = models.CharField('Título', max_length=255)
    description = models.TextField('Descrição', blank=True)
    responsible = models.ForeignKey(
        'accounts.User', verbose_name='Responsável',
        on_delete=models.SET_NULL, null=True, blank=True,
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=Status.choices, default=Status.PENDING,
    )
    due_date = models.DateField('Prazo', null=True, blank=True)
    file = models.FileField('Arquivo', upload_to='contents/', blank=True)
    publication_url = models.URLField('URL de publicação', blank=True)

    class Meta:
        verbose_name = 'Conteúdo'
        verbose_name_plural = 'Conteúdos'
        ordering = ['phase', 'due_date']

    def __str__(self):
        return self.title
