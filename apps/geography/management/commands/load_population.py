"""
Carrega populacao estimada 2022 do IBGE para cidades de SC.
Fonte: IBGE Agregados - Estimativas de Populacao.
Tambem agrega populacao por regiao e macro-regiao.
"""
import gzip
import json
import urllib.request
from django.core.management.base import BaseCommand
from apps.geography.models import City, Region, MacroRegion


class Command(BaseCommand):
    help = 'Carrega populacao das cidades de SC do IBGE (estimativa 2022)'

    def handle(self, *args, **options):
        # Estimativas de populacao 2022 - municipios de SC
        url = 'https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/2022/variaveis/93?localidades=N6[N3[42]]'
        self.stdout.write('Buscando populacao do IBGE...')

        req = urllib.request.Request(url, headers={
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'CRM-Politico/1.0',
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                text = gzip.decompress(raw).decode('utf-8')
            data = json.loads(text)

        series = data[0]['resultados'][0]['series']
        self.stdout.write(f'  {len(series)} municipios encontrados')

        updated = 0
        not_found = 0
        for item in series:
            ibge_code = item['localidade']['id']
            pop = int(list(item['serie'].values())[0])

            try:
                city = City.objects.get(ibge_code=ibge_code)
                city.population = pop
                city.save(update_fields=['population'])
                updated += 1
            except City.DoesNotExist:
                not_found += 1

        self.stdout.write(self.style.SUCCESS(
            f'{updated} cidades atualizadas, {not_found} nao encontradas'
        ))

        # Agregar populacao por regiao
        for region in Region.objects.all():
            region.population = region.cities.aggregate(
                total=__import__('django.db.models', fromlist=['Sum']).Sum('population')
            )['total'] or 0
            region.save(update_fields=['population'])

        self.stdout.write(f'{Region.objects.count()} regioes atualizadas')

        # Agregar por macro-regiao
        for macro in MacroRegion.objects.all():
            macro.population = sum(r.population for r in macro.regions.all())
            macro.save(update_fields=['population'])

        self.stdout.write(self.style.SUCCESS(
            f'{MacroRegion.objects.count()} macro-regioes atualizadas'
        ))
