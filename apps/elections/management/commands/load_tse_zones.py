"""
Importa resultados eleitorais 2022 por zona eleitoral do TSE.
Usa os dados ja baixados por municipio (abr com tpabr=ZONA).
Foco: Deputado Federal (cargo 6) para votos do Sorgatto por zona.
"""
import json
import gzip
import time
import urllib.request
from django.core.management.base import BaseCommand
from apps.elections.models import Election, ZoneResult
from apps.geography.models import City

CARGO_MAP = {
    3: 'governor',
    5: 'senator',
    6: 'federal_deputy',
    7: 'state_deputy',
}

BASE_URL = 'https://resultados.tse.jus.br/oficial/ele2022/546'


class Command(BaseCommand):
    help = 'Importa resultados por zona eleitoral do TSE 2022'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cargos', nargs='+', type=int, default=[6],
            help='Codigos de cargo: 3=Gov, 5=Sen, 6=DepFed, 7=DepEst (default: 6)'
        )
        parser.add_argument(
            '--top', type=int, default=10,
            help='Importar apenas os N candidatos mais votados por zona (0=todos)'
        )

    def _fetch_json(self, url):
        req = urllib.request.Request(url, headers={
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'CRM-Politico/1.0',
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            try:
                data = raw.decode('utf-8')
            except UnicodeDecodeError:
                data = gzip.decompress(raw).decode('utf-8')
            return json.loads(data)

    def handle(self, *args, **options):
        cargos = options['cargos']
        top_n = options['top']

        # Buscar config de municipios
        self.stdout.write('Buscando configuracao de municipios do TSE...')
        config = self._fetch_json(f'{BASE_URL}/config/mun-e000546-cm.json')
        sc_entry = next((a for a in config['abr'] if a['cd'] == 'SC'), None)
        if not sc_entry:
            self.stderr.write('SC nao encontrado')
            return

        tse_municipalities = sc_entry['mu']
        self.stdout.write(f'  {len(tse_municipalities)} municipios')

        # Mapear nomes para City objects
        cities_by_name = {}
        for city in City.objects.all():
            cities_by_name[city.name.upper()] = city

        for cargo_code in cargos:
            if cargo_code not in CARGO_MAP:
                continue

            election_type = CARGO_MAP[cargo_code]
            self.stdout.write(f'\n=== {election_type} - Zonas Eleitorais ===')

            # Buscar dados estaduais para nomes/partidos
            state_url = f'{BASE_URL}/dados-simplificados/sc/sc-c000{cargo_code}-e000546-r.json'
            state_data = self._fetch_json(state_url)
            cand_info = {}
            for c in state_data.get('cand', []):
                cand_info[c['n']] = {
                    'name': c['nm'],
                    'party': c.get('cc', ''),
                    'is_sorgatto': 'sorgatto' in c.get('nm', '').lower(),
                }

            election = Election.objects.get(
                year=2022, election_type=election_type, round_number=1,
            )

            # Limpar zonas anteriores
            ZoneResult.objects.filter(election=election).delete()

            total_results = 0
            errors = 0

            for i, mun in enumerate(tse_municipalities):
                tse_code = mun['cd']
                mun_name = mun['nm']
                zones = mun.get('z', [])

                if not zones:
                    continue

                # Encontrar cidade
                city = cities_by_name.get(mun_name.upper())
                if not city:
                    for db_name, db_city in cities_by_name.items():
                        if mun_name.upper().replace("'", "\u2019") == db_name:
                            city = db_city
                            break
                if not city:
                    continue

                # Buscar dados do municipio (contem zonas)
                mun_url = f'{BASE_URL}/dados/sc/sc{tse_code}-c000{cargo_code}-e000546-v.json'
                try:
                    mun_data = self._fetch_json(mun_url)
                except Exception:
                    errors += 1
                    continue

                abr_list = mun_data.get('abr', [])

                # Filtrar apenas entradas de ZONA
                zone_entries = [a for a in abr_list if a.get('tpabr') == 'ZONA']

                results_to_create = []
                for zone in zone_entries:
                    zone_number = zone.get('cdabr', '')
                    zone_cands = zone.get('cand', [])
                    total_zone_votes = int(zone.get('tv', '0'))

                    # Ordenar por votos e pegar top N
                    zone_cands_sorted = sorted(
                        zone_cands,
                        key=lambda c: int(c.get('vap', '0')),
                        reverse=True
                    )

                    if top_n > 0:
                        selected = zone_cands_sorted[:top_n]
                        # Sempre incluir Sorgatto
                        selected_nums = set(c['n'] for c in selected)
                        for c in zone_cands_sorted:
                            info = cand_info.get(c['n'], {})
                            if info.get('is_sorgatto') and c['n'] not in selected_nums:
                                selected.append(c)
                    else:
                        selected = zone_cands_sorted

                    for mc in selected:
                        cand_num = mc['n']
                        info = cand_info.get(cand_num, {})
                        votes = int(mc.get('vap', '0'))
                        if votes == 0:
                            continue

                        pct = round((votes / total_zone_votes) * 100, 2) if total_zone_votes > 0 else 0

                        results_to_create.append(ZoneResult(
                            election=election,
                            candidate_name=info.get('name', f'#{cand_num}'),
                            candidate_number=cand_num,
                            party=info.get('party', ''),
                            city=city,
                            zone_number=zone_number,
                            votes=votes,
                            percentage=pct,
                            is_sorgatto=info.get('is_sorgatto', False),
                        ))

                if results_to_create:
                    ZoneResult.objects.bulk_create(results_to_create)
                    total_results += len(results_to_create)

                if (i + 1) % 50 == 0:
                    self.stdout.write(f'  {i + 1}/{len(tse_municipalities)} municipios...')

                time.sleep(0.05)

            self.stdout.write(self.style.SUCCESS(
                f'  {total_results} resultados por zona importados ({errors} erros)'
            ))

        self.stdout.write(self.style.SUCCESS('\nImportacao de zonas concluida!'))
