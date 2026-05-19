"""
Importa resultados eleitorais de 2022 do TSE para SC.
Usa a API publica de resultados do TSE para buscar votos por municipio.
Cargos: Governador, Senador, Deputado Federal, Deputado Estadual.
"""
import json
import gzip
import time
import urllib.request
from django.core.management.base import BaseCommand
from apps.elections.models import Election, CandidateResult
from apps.geography.models import City

# Mapeamento de codigos de cargo TSE
CARGO_MAP = {
    3: ('governor', 'Governador'),
    5: ('senator', 'Senador'),
    6: ('federal_deputy', 'Deputado Federal'),
    7: ('state_deputy', 'Deputado Estadual'),
}

BASE_URL = 'https://resultados.tse.jus.br/oficial/ele2022/546'


class Command(BaseCommand):
    help = 'Importa resultados eleitorais 2022 de SC do TSE'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cargos', nargs='+', type=int, default=[3, 5, 6, 7],
            help='Codigos de cargo: 3=Gov, 5=Sen, 6=DepFed, 7=DepEst'
        )
        parser.add_argument(
            '--top', type=int, default=0,
            help='Importar apenas os N candidatos mais votados (0=todos)'
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

        # 1. Buscar mapeamento TSE code -> IBGE code para municipios de SC
        self.stdout.write('Buscando configuracao de municipios do TSE...')
        config = self._fetch_json(f'{BASE_URL}/config/mun-e000546-cm.json')
        sc_entry = next((a for a in config['abr'] if a['cd'] == 'SC'), None)
        if not sc_entry:
            self.stderr.write('SC nao encontrado na config do TSE')
            return

        tse_municipalities = sc_entry['mu']  # [{cd: "80810", nm: "CHAPECÓ"}, ...]
        self.stdout.write(f'  {len(tse_municipalities)} municipios de SC no TSE')

        # Mapear nomes para City objects
        cities_by_name = {}
        for city in City.objects.all():
            cities_by_name[city.name.upper()] = city

        for cargo_code in cargos:
            if cargo_code not in CARGO_MAP:
                self.stderr.write(f'Cargo {cargo_code} nao reconhecido')
                continue

            election_type, cargo_name = CARGO_MAP[cargo_code]
            self.stdout.write(f'\n=== {cargo_name} ===')

            # 2. Buscar dados estaduais para obter nomes e partidos
            state_url = f'{BASE_URL}/dados-simplificados/sc/sc-c000{cargo_code}-e000546-r.json'
            state_data = self._fetch_json(state_url)
            state_cands = state_data.get('cand', [])

            # Mapear numero -> dados do candidato
            cand_info = {}
            for c in state_cands:
                cand_info[c['n']] = {
                    'name': c['nm'],
                    'party': c.get('cc', ''),
                    'elected': c.get('e') == 's',
                    'status': c.get('st', ''),
                    'is_sorgatto': 'sorgatto' in c.get('nm', '').lower(),
                }

            self.stdout.write(f'  {len(cand_info)} candidatos no estado')

            # Filtrar top N se especificado (para reduzir volume)
            if top_n > 0:
                # Ordenar por votos estaduais e pegar top N
                sorted_cands = sorted(state_cands, key=lambda c: int(c.get('vap', '0')), reverse=True)
                top_numbers = set(c['n'] for c in sorted_cands[:top_n])
                # Sempre incluir Sorgatto
                for c in state_cands:
                    if 'sorgatto' in c.get('nm', '').lower():
                        top_numbers.add(c['n'])
                self.stdout.write(f'  Filtrando top {top_n} candidatos')
            else:
                top_numbers = None

            # 3. Criar Election
            election, _ = Election.objects.get_or_create(
                year=2022,
                election_type=election_type,
                round_number=1,
            )

            # Limpar resultados anteriores deste cargo
            CandidateResult.objects.filter(election=election).delete()

            # 4. Buscar votos por municipio
            total_results = 0
            errors = 0

            for i, mun in enumerate(tse_municipalities):
                tse_code = mun['cd']
                mun_name = mun['nm']

                # Encontrar cidade no banco
                city = cities_by_name.get(mun_name.upper())
                if not city:
                    # Tentar variantes de nome
                    for db_name, db_city in cities_by_name.items():
                        if mun_name.upper().replace("'", "'") == db_name:
                            city = db_city
                            break
                if not city:
                    continue

                # Buscar votos do municipio
                mun_url = f'{BASE_URL}/dados/sc/sc{tse_code}-c000{cargo_code}-e000546-v.json'
                try:
                    mun_data = self._fetch_json(mun_url)
                except Exception as e:
                    errors += 1
                    continue

                abr_list = mun_data.get('abr', [])
                if not abr_list:
                    continue

                mun_cands = abr_list[0].get('cand', [])

                results_to_create = []
                for mc in mun_cands:
                    cand_num = mc['n']

                    # Filtrar se top_n ativo
                    if top_numbers and cand_num not in top_numbers:
                        continue

                    info = cand_info.get(cand_num, {})
                    votes = int(mc.get('vap', '0'))

                    if votes == 0:
                        continue

                    results_to_create.append(CandidateResult(
                        election=election,
                        candidate_name=info.get('name', f'Candidato #{cand_num}'),
                        candidate_number=cand_num,
                        party=info.get('party', ''),
                        city=city,
                        votes=votes,
                        percentage=0,  # Calcular depois
                        is_elected=info.get('elected', False),
                        is_sorgatto=info.get('is_sorgatto', False),
                    ))

                if results_to_create:
                    CandidateResult.objects.bulk_create(results_to_create)
                    # Calcular percentuais
                    total_votes = sum(r.votes for r in results_to_create)
                    if total_votes > 0:
                        for r in results_to_create:
                            r.percentage = round((r.votes / total_votes) * 100, 2)
                        CandidateResult.objects.bulk_update(results_to_create, ['percentage'])

                    total_results += len(results_to_create)

                if (i + 1) % 50 == 0:
                    self.stdout.write(f'  {i + 1}/{len(tse_municipalities)} municipios processados...')

                # Rate limiting
                time.sleep(0.05)

            self.stdout.write(self.style.SUCCESS(
                f'  {cargo_name}: {total_results} resultados importados ({errors} erros)'
            ))

            # Atualizar votos_sorgatto_2022 nas cidades (se Dep Federal)
            if cargo_code == 6:
                self._update_sorgatto_votes(election)

        self.stdout.write(self.style.SUCCESS('\nImportacao concluida!'))

    def _update_sorgatto_votes(self, election):
        """Atualiza o campo votes_sorgatto_2022 em cada cidade"""
        sorgatto_results = CandidateResult.objects.filter(
            election=election, is_sorgatto=True
        )
        updated = 0
        for result in sorgatto_results:
            result.city.votes_sorgatto_2022 = result.votes
            result.city.save(update_fields=['votes_sorgatto_2022'])
            updated += 1
        self.stdout.write(f'  {updated} cidades atualizadas com votos Sorgatto 2022')
