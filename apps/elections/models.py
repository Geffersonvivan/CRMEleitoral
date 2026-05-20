from django.db import models
from apps.core.models import TimeStampedModel


class Election(TimeStampedModel):
    class ElectionType(models.TextChoices):
        FEDERAL_DEPUTY = 'federal_deputy', 'Deputado Federal'
        STATE_DEPUTY = 'state_deputy', 'Deputado Estadual'
        SENATOR = 'senator', 'Senador'
        GOVERNOR = 'governor', 'Governador'
        PRESIDENT = 'president', 'Presidente'
        MAYOR = 'mayor', 'Prefeito'
        COUNCILOR = 'councilor', 'Vereador'

    year = models.IntegerField('Ano')
    election_type = models.CharField('Tipo', max_length=20, choices=ElectionType.choices)
    round_number = models.IntegerField('Turno', default=1)

    class Meta:
        verbose_name = 'Eleição'
        verbose_name_plural = 'Eleições'
        unique_together = ['year', 'election_type', 'round_number']

    def __str__(self):
        return f'{self.get_election_type_display()} {self.year} - {self.round_number}o turno'


class CandidateResult(TimeStampedModel):
    election = models.ForeignKey(
        Election, verbose_name='Eleição',
        on_delete=models.CASCADE, related_name='results'
    )
    candidate_name = models.CharField('Candidato', max_length=255)
    candidate_number = models.CharField('Número', max_length=10)
    party = models.CharField('Partido', max_length=150)
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        on_delete=models.CASCADE, related_name='election_results'
    )
    votes = models.IntegerField('Votos', default=0)
    percentage = models.DecimalField('Percentual', max_digits=5, decimal_places=2, default=0)
    is_elected = models.BooleanField('Eleito', default=False)
    is_sorgatto = models.BooleanField('Sorgatto', default=False)

    class Meta:
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'
        ordering = ['-votes']

    def __str__(self):
        return f'{self.candidate_name} - {self.city} ({self.votes} votos)'


class ZoneResult(TimeStampedModel):
    """Resultado de candidato por zona eleitoral em uma cidade"""
    election = models.ForeignKey(
        Election, verbose_name='Eleição',
        on_delete=models.CASCADE, related_name='zone_results'
    )
    candidate_name = models.CharField('Candidato', max_length=255)
    candidate_number = models.CharField('Número', max_length=10)
    party = models.CharField('Partido', max_length=150)
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        on_delete=models.CASCADE, related_name='zone_election_results'
    )
    zone_number = models.CharField('Zona Eleitoral', max_length=10)
    votes = models.IntegerField('Votos', default=0)
    percentage = models.DecimalField('Percentual', max_digits=5, decimal_places=2, default=0)
    is_sorgatto = models.BooleanField('Sorgatto', default=False)

    class Meta:
        verbose_name = 'Resultado por Zona'
        verbose_name_plural = 'Resultados por Zona'
        ordering = ['zone_number', '-votes']

    def __str__(self):
        return f'Zona {self.zone_number} - {self.candidate_name} ({self.votes} votos)'


class VoteGoal(TimeStampedModel):
    class Level(models.TextChoices):
        STATE = 'state', 'Estado'
        MACRO_REGION = 'macro_region', 'Macro Região'
        REGION = 'region', 'Região'
        CITY = 'city', 'Município'
        NEIGHBORHOOD = 'neighborhood', 'Bairro'

    level = models.CharField('Nível', max_length=20, choices=Level.choices)
    macro_region = models.ForeignKey(
        'geography.MacroRegion', null=True, blank=True,
        on_delete=models.CASCADE, related_name='vote_goals'
    )
    region = models.ForeignKey(
        'geography.Region', null=True, blank=True,
        on_delete=models.CASCADE, related_name='vote_goals'
    )
    city = models.ForeignKey(
        'geography.City', null=True, blank=True,
        on_delete=models.CASCADE, related_name='vote_goals'
    )
    neighborhood = models.ForeignKey(
        'geography.Neighborhood', null=True, blank=True,
        on_delete=models.CASCADE, related_name='vote_goals'
    )
    target_votes = models.IntegerField('Meta de votos', default=0)
    current_estimate = models.IntegerField('Estimativa atual', default=0)
    election_year = models.IntegerField('Ano da eleição', default=2026)

    class Meta:
        verbose_name = 'Meta de Votos'
        verbose_name_plural = 'Metas de Votos'

    def __str__(self):
        return f'{self.get_level_display()} - Meta: {self.target_votes}'

    @property
    def progress_percentage(self):
        if self.target_votes == 0:
            return 0
        return round((self.current_estimate / self.target_votes) * 100, 2)
