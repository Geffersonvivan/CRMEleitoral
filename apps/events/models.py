from django.db import models
from apps.core.models import TimeStampedModel, AddressMixin


class Event(TimeStampedModel, AddressMixin):
    class EventType(models.TextChoices):
        RALLY = 'rally', 'Comício'
        MEETING = 'meeting', 'Reunião'
        DOOR_TO_DOOR = 'door_to_door', 'Porta a Porta'
        CARREATA = 'carreata', 'Carreata'
        DEBATE = 'debate', 'Debate'
        COMMUNITY = 'community', 'Evento Comunitário'
        FUNDRAISER = 'fundraiser', 'Evento de Arrecadação'
        TRAINING = 'training', 'Treinamento'

    title = models.CharField('Título', max_length=255)
    event_type = models.CharField('Tipo', max_length=20, choices=EventType.choices)
    description = models.TextField('Descrição', blank=True)
    date = models.DateTimeField('Data/Hora')
    end_date = models.DateTimeField('Data/Hora fim', null=True, blank=True)
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    region = models.ForeignKey(
        'geography.Region', verbose_name='Região',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    expected_attendees = models.IntegerField('Presença esperada', default=0)
    actual_attendees = models.IntegerField('Presença real', default=0)
    organizer = models.ForeignKey(
        'accounts.User', verbose_name='Organizador',
        on_delete=models.SET_NULL, null=True
    )
    contacts_invited = models.ManyToManyField(
        'contacts.Contact', verbose_name='Convidados',
        blank=True, related_name='invited_events'
    )
    contacts_attended = models.ManyToManyField(
        'contacts.Contact', verbose_name='Presentes',
        blank=True, related_name='attended_events'
    )
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} - {self.date:%d/%m/%Y}'
