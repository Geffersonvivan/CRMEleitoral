"""
Carrega macro-regioes e regioes iniciais de SC.
"""
from django.core.management.base import BaseCommand
from apps.geography.models import MacroRegion, Region

MACRO_REGIONS = [
    {"name": "EXTREMO OESTE", "slug": "extremo-oeste", "population": 228161, "color": "#e91e63"},
    {"name": "OESTE", "slug": "oeste", "population": 245004, "color": "#66bb6a"},
    {"name": "MEIO OESTE", "slug": "meio-oeste", "population": 391731, "color": "#ff9800"},
    {"name": "SERRA E PLANALTO", "slug": "serra-planalto", "population": 333223, "color": "#f44336"},
    {"name": "NORTE", "slug": "norte", "population": 1042804, "color": "#9c27b0"},
    {"name": "VALE DO ITAJAI", "slug": "vale-do-itajai", "population": 810071, "color": "#ff5722"},
    {"name": "LITORAL", "slug": "litoral", "population": 1535400, "color": "#ffc107"},
    {"name": "SUL", "slug": "sul", "population": 787928, "color": "#26a69a"},
]

REGIONS = [
    # EXTREMO OESTE
    {"name": "AMEOSC", "full_name": "Associacao dos Municipios do Extremo Oeste Catarinense", "slug": "ameosc", "macro": "extremo-oeste", "population": 137605, "color": "#e91e63"},
    {"name": "AMERIOS", "full_name": "Associacao dos Municipios do Entre Rios", "slug": "amerios", "macro": "extremo-oeste", "population": 90556, "color": "#e91e63"},
    # OESTE
    {"name": "AMNOROESTE", "full_name": "Associacao dos Municipios do Noroeste Catarinense", "slug": "amnoroeste", "macro": "oeste", "population": 41073, "color": "#66bb6a"},
    {"name": "AMOSC", "full_name": "Associacao dos Municipios do Oeste de Santa Catarina", "slug": "amosc", "macro": "oeste", "population": 85752, "color": "#66bb6a"},
    {"name": "AMAI", "full_name": "Associacao dos Municipios do Alto Irani", "slug": "amai", "macro": "oeste", "population": 118179, "color": "#66bb6a"},
    # MEIO OESTE
    {"name": "AMAUC", "full_name": "Associacao dos Municipios do Alto Uruguai Catarinense", "slug": "amauc", "macro": "meio-oeste", "population": 123491, "color": "#ff9800"},
    {"name": "AMMOC", "full_name": "Associacao dos Municipios do Meio Oeste Catarinense", "slug": "ammoc", "macro": "meio-oeste", "population": 100176, "color": "#ff9800"},
    {"name": "AMARP", "full_name": "Associacao dos Municipios do Alto Vale do Rio do Peixe", "slug": "amarp", "macro": "meio-oeste", "population": 168064, "color": "#ff9800"},
    # SERRA E PLANALTO
    {"name": "AMPLASC", "full_name": "Associacao dos Municipios do Planalto Sul de Santa Catarina", "slug": "amplasc", "macro": "serra-planalto", "population": 47219, "color": "#f44336"},
    {"name": "AMURC", "full_name": "Associacao dos Municipios da Regiao do Contestado", "slug": "amurc", "macro": "serra-planalto", "population": 52798, "color": "#f44336"},
    {"name": "AMURES", "full_name": "Associacao dos Municipios da Regiao Serrana", "slug": "amures", "macro": "serra-planalto", "population": 233206, "color": "#f44336"},
    # NORTE
    {"name": "AMPLANORTE", "full_name": "Associacao dos Municipios do Planalto Norte Catarinense", "slug": "amplanorte", "macro": "norte", "population": 182399, "color": "#9c27b0"},
    {"name": "AMUNESC", "full_name": "Associacao dos Municipios do Nordeste de Santa Catarina", "slug": "amunesc", "macro": "norte", "population": 637925, "color": "#9c27b0"},
    {"name": "AMVALI", "full_name": "Associacao dos Municipios do Vale do Itapocu", "slug": "amvali", "macro": "norte", "population": 223380, "color": "#9c27b0"},
    # VALE DO ITAJAI
    {"name": "AMAVI", "full_name": "Associacao dos Municipios do Alto Vale do Itajai", "slug": "amavi", "macro": "vale-do-itajai", "population": 231142, "color": "#ff5722"},
    {"name": "AMVE", "full_name": "Associacao dos Municipios do Vale Europeu", "slug": "amve", "macro": "vale-do-itajai", "population": 578929, "color": "#ff5722"},
    # LITORAL
    {"name": "AMFRI", "full_name": "Associacao dos Municipios da Foz do Rio Itajai", "slug": "amfri", "macro": "litoral", "population": 574585, "color": "#ffc107"},
    {"name": "GRANFPOLIS", "full_name": "Associacao dos Municipios da Grande Florianopolis", "slug": "granfpolis", "macro": "litoral", "population": 960815, "color": "#ffc107"},
    # SUL
    {"name": "AMUREL", "full_name": "Associacao dos Municipios da Regiao de Laguna", "slug": "amurel", "macro": "sul", "population": 290117, "color": "#26a69a"},
    {"name": "AMREC", "full_name": "Associacao dos Municipios da Regiao Carbonifera", "slug": "amrec", "macro": "sul", "population": 331644, "color": "#26a69a"},
    {"name": "AMESC", "full_name": "Associacao dos Municipios do Extremo Sul Catarinense", "slug": "amesc", "macro": "sul", "population": 166167, "color": "#26a69a"},
]


class Command(BaseCommand):
    help = 'Carrega macro-regioes e regioes de SC'

    def handle(self, *args, **options):
        # Macro regioes
        for mr_data in MACRO_REGIONS:
            mr, created = MacroRegion.objects.update_or_create(
                slug=mr_data['slug'],
                defaults=mr_data,
            )
            status = 'CRIADA' if created else 'ATUALIZADA'
            self.stdout.write(f'  Macro Regiao {mr.name} - {status}')

        # Regioes
        macro_map = {mr.slug: mr for mr in MacroRegion.objects.all()}
        for r_data in REGIONS:
            macro_slug = r_data.pop('macro')
            r_data['macro_region'] = macro_map[macro_slug]
            region, created = Region.objects.update_or_create(
                slug=r_data['slug'],
                defaults=r_data,
            )
            status = 'CRIADA' if created else 'ATUALIZADA'
            self.stdout.write(f'  Regiao {region.name} - {status}')

        self.stdout.write(self.style.SUCCESS(
            f'\n{MacroRegion.objects.count()} macro-regioes, {Region.objects.count()} regioes carregadas.'
        ))
