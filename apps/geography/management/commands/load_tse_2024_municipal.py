"""
Importa dados eleitorais municipais 2024 do TSE para o model City.

Dados importados:
  - mayor_name: nome de urna do prefeito eleito
  - mayor_party: partido do prefeito eleito
  - num_vereadores: total de vereadores eleitos
  - num_vereadores_pl: total de vereadores eleitos pelo PL
  - registered_voters: total de eleitores por municipio

Fonte: TSE Dados Abertos - Eleicoes 2024
  Candidatos: data/tse2024/consulta_cand_2024_SC.csv
  Eleitorado: data/tse2024/perfil_eleitorado_2024.csv
"""
import csv
import unicodedata
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.geography.models import City


def normalize_name(name):
    """Remove acentos e converte para uppercase para comparacao."""
    return unicodedata.normalize('NFKD', name.upper()).encode('ascii', 'ignore').decode()


class Command(BaseCommand):
    help = 'Importa prefeitos e vereadores eleitos 2024 do TSE para o model City'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            default='data/tse2024/consulta_cand_2024_SC.csv',
            help='Caminho do CSV de candidatos TSE 2024',
        )
        parser.add_argument(
            '--eleitorado-csv',
            default='data/tse2024/perfil_eleitorado_2024.csv',
            help='Caminho do CSV de perfil do eleitorado TSE 2024',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria importado, sem salvar',
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        dry_run = options['dry_run']

        # Ler CSV do TSE
        self.stdout.write(f'Lendo {csv_path}...')
        rows = []
        with open(csv_path, encoding='latin-1') as f:
            reader = csv.DictReader(f, delimiter=';', quotechar='"')
            for row in reader:
                rows.append(row)
        self.stdout.write(f'  {len(rows)} linhas lidas')

        # Extrair prefeitos eleitos (pegar maior turno por cidade)
        prefeitos = {}  # city_name -> {name, party, turno}
        for row in rows:
            if row['DS_CARGO'] != 'PREFEITO':
                continue
            if row['DS_SIT_TOT_TURNO'] != 'ELEITO':
                continue
            city = row['NM_UE'].strip()
            turno = int(row['NR_TURNO'])
            existing = prefeitos.get(city)
            if not existing or turno > existing['turno']:
                prefeitos[city] = {
                    'name': row['NM_URNA_CANDIDATO'].strip(),
                    'party': row['SG_PARTIDO'].strip(),
                    'turno': turno,
                }
        self.stdout.write(f'  {len(prefeitos)} prefeitos eleitos encontrados')

        # Extrair vereadores eleitos
        situacoes_eleito = {'ELEITO', 'ELEITO POR MÉDIA', 'ELEITO POR QP'}
        vereadores = defaultdict(lambda: {'total': 0, 'pl': 0})
        for row in rows:
            if row['DS_CARGO'] != 'VEREADOR':
                continue
            if row['DS_SIT_TOT_TURNO'] not in situacoes_eleito:
                continue
            city = row['NM_UE'].strip()
            vereadores[city]['total'] += 1
            if row['SG_PARTIDO'].strip() == 'PL':
                vereadores[city]['pl'] += 1
        self.stdout.write(f'  {len(vereadores)} cidades com vereadores eleitos')

        # Extrair eleitorado por municipio (arquivo grande, ler streaming filtrando SC)
        eleitorado = defaultdict(int)
        eleitorado_csv = options['eleitorado_csv']
        import os
        if os.path.exists(eleitorado_csv):
            self.stdout.write(f'Lendo eleitorado {eleitorado_csv}...')
            with open(eleitorado_csv, encoding='latin-1') as f:
                reader = csv.DictReader(f, delimiter=';', quotechar='"')
                for row in reader:
                    if row['SG_UF'] == 'SC':
                        city = row['NM_MUNICIPIO'].strip()
                        eleitorado[city] += int(row['QT_ELEITORES_PERFIL'])
            self.stdout.write(f'  {len(eleitorado)} cidades com dados de eleitorado')
        else:
            self.stdout.write(self.style.WARNING(
                f'Arquivo de eleitorado nao encontrado: {eleitorado_csv} (pulando registered_voters)'
            ))

        # Carregar cidades do banco e criar lookup por nome normalizado
        cities = {normalize_name(c.name): c for c in City.objects.all()}
        self.stdout.write(f'  {len(cities)} cidades no banco')

        updated = []
        not_found = []

        # Unir todas as cidades do TSE
        all_tse_cities = set(prefeitos.keys()) | set(vereadores.keys()) | set(eleitorado.keys())

        for tse_name in sorted(all_tse_cities):
            norm = normalize_name(tse_name)
            city = cities.get(norm)
            if not city:
                not_found.append(tse_name)
                continue

            changed = False

            # Prefeito
            pref = prefeitos.get(tse_name)
            if pref:
                if city.mayor_name != pref['name'] or city.mayor_party != pref['party']:
                    city.mayor_name = pref['name']
                    city.mayor_party = pref['party']
                    changed = True

            # Vereadores
            ver = vereadores.get(tse_name)
            if ver:
                if city.num_vereadores != ver['total'] or city.num_vereadores_pl != ver['pl']:
                    city.num_vereadores = ver['total']
                    city.num_vereadores_pl = ver['pl']
                    changed = True

            # Eleitorado
            eleit = eleitorado.get(tse_name)
            if eleit and city.registered_voters != eleit:
                city.registered_voters = eleit
                changed = True

            if changed:
                updated.append(city)

        if not_found:
            self.stderr.write(self.style.WARNING(
                f'\n{len(not_found)} cidades TSE sem correspondencia no banco:'
            ))
            for name in not_found:
                self.stderr.write(f'  - {name}')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] {len(updated)} cidades seriam atualizadas'))
            for city in updated[:20]:
                self.stdout.write(
                    f'  {city.name}: prefeito={city.mayor_name} ({city.mayor_party}), '
                    f'vereadores={city.num_vereadores} (PL: {city.num_vereadores_pl}), '
                    f'eleitores={city.registered_voters:,}'
                )
            if len(updated) > 20:
                self.stdout.write(f'  ... e mais {len(updated) - 20}')
            return

        if updated:
            City.objects.bulk_update(
                updated,
                ['mayor_name', 'mayor_party', 'num_vereadores', 'num_vereadores_pl', 'registered_voters'],
            )
            self.stdout.write(self.style.SUCCESS(f'\n{len(updated)} cidades atualizadas com sucesso!'))
        else:
            self.stdout.write(self.style.SUCCESS('\nNenhuma cidade precisou ser atualizada.'))
