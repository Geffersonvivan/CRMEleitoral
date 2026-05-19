"""
Carrega os bairros de Chapeco conforme o mapa de articulacao.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.geography.models import City, Neighborhood

CHAPECO_BAIRROS = [
    'Trevo', 'Belvedere', 'Vila Rica', 'Esplanada', 'Dom Gerônimo',
    'Água Santa', 'Eldorado', 'Bom Retiro', 'Desbravador', 'Vila Real',
    'Cristo Rei', 'Bela Vista', 'Alvorada', 'Lider', 'Santa Paulina',
    'Lageado', 'Jardim Europa', 'Passo dos Fortes', 'Pinheirinho',
    'Presidente Medici', 'Sao Cristovao', 'Paraiso', 'Maria Goretti',
    'Centro', 'Jardim America', 'Saic', 'Jardim Italia',
    'Santo Antonio', 'Santa Maria', 'Boa Vista', 'Sao Lucas',
    'Sao Pedro', 'Bom Pastor', 'Monte Belo', 'Universitario',
    'Quedas do Palmital', 'Palmital', 'Dom Pascoal', 'Seminario',
    'Santos Dumont', 'Campestre', 'Progresso', 'Industrial',
    'Efapi', 'Engenho Braun', 'Parque das Palmeiras',
    'Jardins', 'Fronteira Sul', 'Autódromo', 'Araras',
]


class Command(BaseCommand):
    help = 'Carrega bairros de Chapecó'

    def handle(self, *args, **options):
        try:
            chapeco = City.objects.get(name='Chapecó')
        except City.DoesNotExist:
            try:
                chapeco = City.objects.filter(name__icontains='Chapecó').exclude(name__icontains='Águas').first()
                if not chapeco:
                    raise City.DoesNotExist
            except City.DoesNotExist:
                self.stderr.write('Cidade de Chapecó não encontrada. Execute load_sc_cities primeiro.')
                return

        created = 0
        for bairro_name in CHAPECO_BAIRROS:
            _, was_created = Neighborhood.objects.get_or_create(
                slug=slugify(bairro_name),
                city=chapeco,
                defaults={'name': bairro_name},
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'{created} bairros criados para Chapecó'))
