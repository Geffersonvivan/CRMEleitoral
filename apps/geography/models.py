from django.db import models
from apps.core.models import TimeStampedModel


class MacroRegion(TimeStampedModel):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField(unique=True)
    population = models.IntegerField('População', default=0)
    geojson = models.JSONField('GeoJSON', null=True, blank=True)
    color = models.CharField('Cor', max_length=7, default='#3388ff')

    class Meta:
        verbose_name = 'Macro Região'
        verbose_name_plural = 'Macro Regiões'
        ordering = ['name']

    def __str__(self):
        return self.name


class Region(TimeStampedModel):
    name = models.CharField('Sigla', max_length=100)
    full_name = models.CharField('Nome completo', max_length=255, blank=True)
    slug = models.SlugField(unique=True)
    macro_region = models.ForeignKey(
        MacroRegion, verbose_name='Macro Região',
        on_delete=models.CASCADE, related_name='regions'
    )
    population = models.IntegerField('População', default=0)
    geojson = models.JSONField('GeoJSON', null=True, blank=True)
    svg_path_id = models.CharField('ID no SVG', max_length=50, blank=True)
    coordinator = models.ForeignKey(
        'contacts.Contact', verbose_name='Coordenador',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='coordinated_regions'
    )
    meta_votes = models.IntegerField('Meta de votos', default=0)
    meta_doacoes = models.DecimalField('Meta de doações (R$)', max_digits=12, decimal_places=2, default=0)
    color = models.CharField('Cor', max_length=7, default='#3388ff')

    class Meta:
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'
        ordering = ['name']

    def __str__(self):
        return self.name


class City(TimeStampedModel):
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField(db_index=True)
    ibge_code = models.CharField('Código IBGE', max_length=10, unique=True)
    region = models.ForeignKey(
        Region, verbose_name='Região',
        on_delete=models.CASCADE, related_name='cities'
    )
    population = models.IntegerField('População', default=0)
    registered_voters = models.IntegerField('Eleitores', default=0)
    geojson = models.JSONField('GeoJSON', null=True, blank=True)
    mayor_name = models.CharField('Prefeito', max_length=200, blank=True)
    mayor_party = models.CharField('Partido do prefeito', max_length=50, blank=True)
    num_vereadores = models.IntegerField('Vereadores', default=0)
    num_vereadores_pl = models.IntegerField('Vereadores PL', default=0)
    pl_executive_president = models.CharField('Presidente executiva PL', max_length=200, blank=True)
    economic_matrix = models.TextField('Matriz econômica', blank=True)
    votes_sorgatto_2022 = models.IntegerField('Votos Sorgatto 2022', default=0)
    meta_votes = models.IntegerField('Meta de votos', default=0)
    electoral_zone = models.CharField('Zona eleitoral', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        ordering = ['name']
        unique_together = ['slug', 'region']

    def __str__(self):
        return f'{self.name} ({self.region.name})'


class Neighborhood(TimeStampedModel):
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField(db_index=True)
    city = models.ForeignKey(
        City, verbose_name='Cidade',
        on_delete=models.CASCADE, related_name='neighborhoods'
    )
    population = models.IntegerField('População', default=0)
    geojson = models.JSONField('GeoJSON', null=True, blank=True)
    coordinator = models.ForeignKey(
        'contacts.Contact', verbose_name='Coordenador',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='coordinated_neighborhoods'
    )
    meta_votes = models.IntegerField('Meta de votos', default=0)

    class Meta:
        verbose_name = 'Bairro'
        verbose_name_plural = 'Bairros'
        ordering = ['name']
        unique_together = ['slug', 'city']

    def __str__(self):
        return f'{self.name} - {self.city.name}'


class ElectoralZone(TimeStampedModel):
    zone_number = models.CharField('Número da zona', max_length=10)
    city = models.ForeignKey(
        City, verbose_name='Cidade',
        on_delete=models.CASCADE, related_name='electoral_zones'
    )
    registered_voters = models.IntegerField('Eleitores', default=0)
    location = models.CharField('Local', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Zona Eleitoral'
        verbose_name_plural = 'Zonas Eleitorais'

    def __str__(self):
        return f'Zona {self.zone_number} - {self.city.name}'
