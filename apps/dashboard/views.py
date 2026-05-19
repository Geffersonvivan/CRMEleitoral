from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import models
from django.db.models import Count, Sum, Q, Max, F
from apps.contacts.models import Contact, CompanyPartner
from apps.geography.models import Region, City
from apps.elections.models import VoteGoal, CandidateResult, Election, ZoneResult
from apps.campaigns.models import Task, ItineraryStop


class DashboardOverviewAPI(APIView):
    def get(self, request):
        # Uma unica query com Count condicional em vez de 8 queries separadas
        counts = Contact.objects.filter(is_active=True).aggregate(
            total_contatos=Count('id'),
            coordenadores=Count('id', filter=Q(category__startswith='coordenador')),
            apoiadores=Count('id', filter=Q(category='apoiador')),
            parceiros=Count('id', filter=Q(category='parceiro')),
            liderancas=Count('id', filter=Q(category='lideranca')),
            eleitores=Count('id', filter=Q(category='eleitor')),
            indecisos=Count('id', filter=Q(category='indeciso')),
        )
        data = {
            **counts,
            'empresas_parceiras': CompanyPartner.objects.count(),
            'regions': list(
                Region.objects.select_related('macro_region').annotate(
                    total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
                    total_votes_2022=Sum('cities__votes_sorgatto_2022'),
                ).values(
                    'name', 'slug', 'population', 'meta_votes', 'color',
                    'total_contacts', 'total_votes_2022',
                    macro_region_name=models.F('macro_region__name'),
                ).order_by('name')
            ),
        }
        return Response(data)


class RegionDashboardAPI(APIView):
    def get(self, request, slug):
        region = Region.objects.get(slug=slug)
        # Uma unica query com Count condicional
        counts = Contact.objects.filter(region=region, is_active=True).aggregate(
            total_contatos=Count('id'),
            coordenadores=Count('id', filter=Q(category__startswith='coordenador')),
            apoiadores=Count('id', filter=Q(category='apoiador')),
        )
        cities = region.cities.annotate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
            total_apoiadores=Count('contacts', filter=Q(contacts__category='apoiador', contacts__is_active=True)),
        )
        data = {
            'region': {
                'name': region.name,
                'full_name': region.full_name,
                'population': region.population,
                'meta_votes': region.meta_votes,
            },
            **counts,
            'cities': list(cities.values(
                'name', 'slug', 'population', 'votes_sorgatto_2022',
                'meta_votes', 'total_contacts', 'total_apoiadores'
            )),
        }
        return Response(data)


class CityDashboardAPI(APIView):
    def get(self, request, slug):
        city = City.objects.select_related('region', 'region__macro_region').get(slug=slug)

        # Uma unica query com Count condicional + by_category
        counts = Contact.objects.filter(city=city, is_active=True).aggregate(
            total_contatos=Count('id'),
            coordenadores=Count('id', filter=Q(category__startswith='coordenador')),
            apoiadores=Count('id', filter=Q(category='apoiador')),
        )

        by_category = list(
            Contact.objects.filter(city=city, is_active=True)
            .values('category').annotate(total=Count('id')).order_by('-total')
        )

        # Resultados eleitorais 2022 - uma unica query com select_related
        election_results = {}
        all_results = (
            CandidateResult.objects
            .filter(election__year=2022, city=city)
            .select_related('election')
            .order_by('election__election_type', '-votes')
        )
        sorgatto_by_type = {}
        position_counter = {}
        for r in all_results:
            key = r.election.get_election_type_display()
            if key not in election_results:
                election_results[key] = []
                position_counter[key] = 0
            position_counter[key] += 1
            entry = {
                'name': r.candidate_name,
                'number': r.candidate_number,
                'party': r.party,
                'votes': r.votes,
                'percentage': float(r.percentage),
                'is_elected': r.is_elected,
                'is_sorgatto': r.is_sorgatto,
                'position': position_counter[key],
            }
            if r.is_sorgatto:
                sorgatto_by_type[key] = entry
            if len(election_results[key]) < 20:
                election_results[key].append(entry)

        # Garantir que LS sempre aparece (mesmo fora do top 20)
        for key, ls_entry in sorgatto_by_type.items():
            already_in = any(e.get('is_sorgatto') for e in election_results.get(key, []))
            if not already_in:
                election_results[key].append(ls_entry)

        # Resultados por zona eleitoral
        zone_results = {}
        zone_qs = ZoneResult.objects.filter(city=city).order_by('zone_number', '-votes')
        for zr in zone_qs:
            zone_key = zr.zone_number
            if zone_key not in zone_results:
                zone_results[zone_key] = {
                    'zone_number': zone_key,
                    'candidates': [],
                    'sorgatto_votes': 0,
                    'total_votes': 0,
                }
            zone_results[zone_key]['candidates'].append({
                'name': zr.candidate_name,
                'number': zr.candidate_number,
                'party': zr.party,
                'votes': zr.votes,
                'percentage': float(zr.percentage),
                'is_sorgatto': zr.is_sorgatto,
            })
            zone_results[zone_key]['total_votes'] += zr.votes
            if zr.is_sorgatto:
                zone_results[zone_key]['sorgatto_votes'] = zr.votes
        zones_list = sorted(zone_results.values(), key=lambda z: z['zone_number'])

        # === ANÁLISE ESTRATÉGICA ===
        strategic = self._build_strategic(city, counts)

        # === DEPUTADOS ALIADOS ===
        allies = self._build_allies(city)

        data = {
            'city': {
                'name': city.name,
                'slug': city.slug,
                'region': city.region.name,
                'region_slug': city.region.slug,
                'macro_region': city.region.macro_region.name,
                'population': city.population,
                'registered_voters': city.registered_voters,
                'mayor_name': city.mayor_name,
                'mayor_party': city.mayor_party,
                'num_vereadores': city.num_vereadores,
                'num_vereadores_pl': city.num_vereadores_pl,
                'pl_executive_president': city.pl_executive_president,
                'economic_matrix': city.economic_matrix,
                'votes_sorgatto_2022': city.votes_sorgatto_2022,
                'meta_votes': city.meta_votes,
            },
            **counts,
            'by_category': by_category,
            'election_results': election_results,
            'zone_results': zones_list,
            'strategic': strategic,
            'allies': allies,
        }
        return Response(data)

    def _build_strategic(self, city, counts):
        today = timezone.now().date()

        # --- 1. Potencial Eleitoral ---
        votes_2022 = city.votes_sorgatto_2022 or 0
        meta = city.meta_votes or 0
        voters = city.registered_voters or 0
        votes_needed = max(meta - votes_2022, 0)
        growth_pct = round((votes_needed / votes_2022 * 100), 1) if votes_2022 > 0 else 0
        penetration = round((votes_2022 / voters * 100), 2) if voters > 0 else 0

        # Meta estadual total
        state_totals = City.objects.aggregate(
            total_meta=Sum('meta_votes'),
            total_votes=Sum('votes_sorgatto_2022'),
            total_voters=Sum('registered_voters'),
        )
        total_meta = state_totals['total_meta'] or 1
        pct_of_state_goal = round(meta / total_meta * 100, 2)
        avg_penetration = round(
            (state_totals['total_votes'] or 0) / max(state_totals['total_voters'] or 1, 1) * 100, 2
        )

        # Ranking na região por crescimento necessário (menor gap = mais consolidada)
        region_cities = list(
            City.objects.filter(region=city.region)
            .values('slug', 'name', 'votes_sorgatto_2022', 'meta_votes')
            .order_by('-votes_sorgatto_2022')
        )
        region_ranking = 0
        for i, rc in enumerate(region_cities, 1):
            if rc['slug'] == city.slug:
                region_ranking = i
                break

        potential = {
            'votes_2022': votes_2022,
            'meta_2026': meta,
            'votes_needed': votes_needed,
            'growth_pct': growth_pct,
            'penetration': penetration,
            'avg_penetration': avg_penetration,
            'pct_of_state_goal': pct_of_state_goal,
            'region_ranking': region_ranking,
            'region_total_cities': len(region_cities),
        }

        # --- 2. Estrutura Política ---
        mayor_party = (city.mayor_party or '').upper().strip()
        if mayor_party in ALLIED_PARTIES:
            alignment = 'allied'
        elif mayor_party in ADVERSARY_PARTIES:
            alignment = 'adversary'
        else:
            alignment = 'neutral'

        has_coordinator = Contact.objects.filter(
            city=city, is_active=True,
            category__in=['coordenador_regional', 'coordenador_municipal']
        ).exists()

        coordinator_name = ''
        coord = Contact.objects.filter(
            city=city, is_active=True,
            category__in=['coordenador_regional', 'coordenador_municipal']
        ).first()
        if coord:
            coordinator_name = coord.full_name

        # Vereadores de partidos aliados/adversários
        # (não temos modelo de vereadores individuais, usamos num_vereadores_pl)
        structure = {
            'alignment': alignment,
            'alignment_label': {'allied': 'Aliado', 'adversary': 'Adversário', 'neutral': 'Neutro'}[alignment],
            'mayor_name': city.mayor_name or '',
            'mayor_party': city.mayor_party or '',
            'num_vereadores': city.num_vereadores or 0,
            'num_vereadores_pl': city.num_vereadores_pl or 0,
            'pl_executive_president': city.pl_executive_president or '',
            'has_coordinator': has_coordinator,
            'coordinator_name': coordinator_name,
        }

        # --- 3. Análise Eleitoral Comparativa (Deputado Estadual 2022) ---
        state_dep_results = list(
            CandidateResult.objects
            .filter(
                election__year=2022,
                election__election_type='state_deputy',
                city=city,
            )
            .select_related('election')
            .order_by('-votes')[:10]
        )
        ls_state_dep = None
        top_candidates = []
        for i, r in enumerate(state_dep_results):
            entry = {
                'position': i + 1,
                'name': r.candidate_name,
                'number': r.candidate_number,
                'party': r.party,
                'votes': r.votes,
                'percentage': float(r.percentage),
                'is_elected': r.is_elected,
                'is_sorgatto': r.is_sorgatto,
                'is_allied': r.party.upper().strip() in ALLIED_PARTIES,
                'is_adversary': r.party.upper().strip() in ADVERSARY_PARTIES,
            }
            top_candidates.append(entry)
            if r.is_sorgatto:
                ls_state_dep = entry

        # Se LS não está no top 10, buscar separadamente
        if not ls_state_dep:
            ls_result = (
                CandidateResult.objects
                .filter(
                    election__year=2022,
                    election__election_type='state_deputy',
                    city=city,
                    is_sorgatto=True,
                )
                .first()
            )
            if ls_result:
                # Posição real
                ls_pos = CandidateResult.objects.filter(
                    election=ls_result.election,
                    city=city,
                    votes__gt=ls_result.votes,
                ).count() + 1
                ls_state_dep = {
                    'position': ls_pos,
                    'name': ls_result.candidate_name,
                    'number': ls_result.candidate_number,
                    'party': ls_result.party,
                    'votes': ls_result.votes,
                    'percentage': float(ls_result.percentage),
                    'is_elected': ls_result.is_elected,
                    'is_sorgatto': True,
                    'is_allied': True,
                    'is_adversary': False,
                }

        # Also check federal deputy if no state deputy data
        if not top_candidates:
            fed_dep_results = list(
                CandidateResult.objects
                .filter(
                    election__year=2022,
                    election__election_type='federal_deputy',
                    city=city,
                )
                .select_related('election')
                .order_by('-votes')[:10]
            )
            for i, r in enumerate(fed_dep_results):
                entry = {
                    'position': i + 1,
                    'name': r.candidate_name,
                    'number': r.candidate_number,
                    'party': r.party,
                    'votes': r.votes,
                    'percentage': float(r.percentage),
                    'is_elected': r.is_elected,
                    'is_sorgatto': r.is_sorgatto,
                    'is_allied': r.party.upper().strip() in ALLIED_PARTIES,
                    'is_adversary': r.party.upper().strip() in ADVERSARY_PARTIES,
                }
                top_candidates.append(entry)
                if r.is_sorgatto:
                    ls_state_dep = entry

        gap_to_first = 0
        first_candidate = top_candidates[0] if top_candidates else None
        if first_candidate and ls_state_dep and not first_candidate.get('is_sorgatto'):
            gap_to_first = (first_candidate['votes'] or 0) - (ls_state_dep['votes'] or 0)

        # O primeiro colocado é aliado?
        first_is_allied = first_candidate['is_allied'] if first_candidate else False
        first_is_adversary = first_candidate['is_adversary'] if first_candidate else False

        electoral_comparison = {
            'election_type': 'Deputado Estadual' if state_dep_results else 'Deputado Federal',
            'top_candidates': top_candidates,
            'ls_result': ls_state_dep,
            'gap_to_first': gap_to_first,
            'first_is_allied': first_is_allied,
            'first_is_adversary': first_is_adversary,
        }

        # --- 4. Indicadores de Atividade ---
        total_contacts = counts.get('total_contatos', 0)
        contact_coverage = round(total_contacts / max(voters, 1) * 100, 2)

        # Demandas
        demands_total = Task.objects.filter(city=city).count()
        demands_completed = Task.objects.filter(city=city, phase='completed').count()
        demands_overdue = Task.objects.filter(
            city=city, due_date__lt=today
        ).exclude(phase='completed').count()
        demands_open = demands_total - demands_completed

        # Visitas (ItineraryStop)
        visits = ItineraryStop.objects.filter(city=city)
        visits_total = visits.count()
        visits_completed = visits.filter(
            itinerary__status__in=['completed', 'in_progress']
        ).count()
        last_visit_date = visits.aggregate(last=Max('date'))['last']

        # Dias sem visita
        days_since_visit = None
        if last_visit_date:
            days_since_visit = (today - last_visit_date).days

        # Interações recentes
        from apps.contacts.models import Interaction
        interactions_count = Interaction.objects.filter(
            contact__city=city,
        ).count()
        last_interaction = Interaction.objects.filter(
            contact__city=city,
        ).aggregate(last=Max('created_at'))['last']

        activity = {
            'contact_coverage': contact_coverage,
            'total_contacts': total_contacts,
            'demands_total': demands_total,
            'demands_completed': demands_completed,
            'demands_open': demands_open,
            'demands_overdue': demands_overdue,
            'visits_total': visits_total,
            'visits_completed': visits_completed,
            'last_visit_date': last_visit_date.isoformat() if last_visit_date else None,
            'days_since_visit': days_since_visit,
            'interactions_count': interactions_count,
            'last_interaction': last_interaction.isoformat() if last_interaction else None,
        }

        # --- 5. Score Detalhado ---
        align_score_raw = {'allied': 100, 'neutral': 50, 'adversary': 0}[alignment]
        vereadores_pct = round(
            (city.num_vereadores_pl / city.num_vereadores * 100) if city.num_vereadores else 0, 1
        )
        pen_normalized = round(min(penetration / max(avg_penetration * 2, 0.01) * 100, 100), 1)
        has_structure_val = 100 if city.pl_executive_president else 0

        align_weighted = round(align_score_raw * 0.30)
        vereadores_weighted = round(vereadores_pct * 0.20)
        pen_weighted = round(pen_normalized * 0.35)
        structure_weighted = round(has_structure_val * 0.15)
        total_score = align_weighted + vereadores_weighted + pen_weighted + structure_weighted

        score_detail = {
            'total': total_score,
            'components': [
                {
                    'label': 'Alinhamento político',
                    'raw': align_score_raw,
                    'weight': 30,
                    'weighted': align_weighted,
                    'max': 30,
                },
                {
                    'label': 'Penetração 2022',
                    'raw': round(pen_normalized, 1),
                    'weight': 35,
                    'weighted': pen_weighted,
                    'max': 35,
                },
                {
                    'label': 'Vereadores PL',
                    'raw': round(vereadores_pct, 1),
                    'weight': 20,
                    'weighted': vereadores_weighted,
                    'max': 20,
                },
                {
                    'label': 'Estrutura PL',
                    'raw': has_structure_val,
                    'weight': 15,
                    'weighted': structure_weighted,
                    'max': 15,
                },
            ],
        }

        # --- 6. Classificação e Recomendação ---
        good_performance = penetration >= avg_penetration
        if alignment == 'allied' and good_performance:
            classification = 'base_forte'
        elif alignment == 'adversary' and good_performance:
            classification = 'potencial_oculto'
        elif alignment == 'allied' and not good_performance:
            classification = 'aliado_fraco'
        elif alignment == 'adversary' and not good_performance:
            classification = 'territorio_hostil'
        else:
            classification = 'potencial_oculto' if good_performance else 'neutro'

        classification_labels = {
            'base_forte': 'Base Forte',
            'aliado_fraco': 'Aliado Fraco',
            'potencial_oculto': 'Potencial Oculto',
            'territorio_hostil': 'Território Hostil',
            'neutro': 'Neutro',
        }

        # Gerar recomendações automáticas
        recommendations = []

        if not has_coordinator:
            recommendations.append({
                'priority': 'urgent',
                'icon': 'alert',
                'text': 'Designar coordenador municipal — cidade sem representante ativo.',
            })

        if classification == 'base_forte' and days_since_visit and days_since_visit > 60:
            recommendations.append({
                'priority': 'medium',
                'icon': 'calendar',
                'text': f'Manter presença — última visita há {days_since_visit} dias. Agendar visita de manutenção.',
            })
        elif classification == 'base_forte' and not last_visit_date:
            recommendations.append({
                'priority': 'medium',
                'icon': 'calendar',
                'text': 'Base forte sem registro de visita. Agendar presença para manutenção.',
            })

        if classification == 'potencial_oculto':
            recommendations.append({
                'priority': 'high',
                'icon': 'target',
                'text': 'Prioridade alta — cidade com bom desempenho em 2022 mas sem apoio político local. Investir em articulação.',
            })

        if classification == 'aliado_fraco':
            if has_coordinator:
                recommendations.append({
                    'priority': 'high',
                    'icon': 'trending-up',
                    'text': 'Intensificar articulação — tem estrutura aliada mas resultado aquém da média.',
                })
            else:
                recommendations.append({
                    'priority': 'high',
                    'icon': 'trending-up',
                    'text': 'Aliado fraco sem coordenador — designar coordenador e montar plano de crescimento.',
                })

        if classification == 'territorio_hostil':
            if votes_2022 > 500:
                recommendations.append({
                    'priority': 'medium',
                    'icon': 'shield',
                    'text': f'Território adversário com {votes_2022} votos em 2022. Manter base existente com contato direto.',
                })
            else:
                recommendations.append({
                    'priority': 'low',
                    'icon': 'minus',
                    'text': 'Baixa prioridade — investir apenas se houver oportunidade pontual.',
                })

        if classification == 'neutro':
            if good_performance:
                recommendations.append({
                    'priority': 'medium',
                    'icon': 'search',
                    'text': 'Cidade neutra com bom desempenho. Buscar aliança com lideranças locais.',
                })
            else:
                recommendations.append({
                    'priority': 'low',
                    'icon': 'clock',
                    'text': 'Cidade neutra com baixo desempenho. Monitorar e atuar se surgir oportunidade.',
                })

        if demands_overdue > 0:
            recommendations.append({
                'priority': 'urgent',
                'icon': 'alert',
                'text': f'{demands_overdue} demanda(s) em atraso nesta cidade. Resolver para manter credibilidade.',
            })

        if contact_coverage < 0.5 and voters > 5000:
            recommendations.append({
                'priority': 'medium',
                'icon': 'users',
                'text': f'Cobertura de contatos muito baixa ({contact_coverage:.2f}%). Intensificar captação.',
            })

        if first_is_adversary and ls_state_dep and gap_to_first > 0:
            recommendations.append({
                'priority': 'high',
                'icon': 'flag',
                'text': f'Deputado mais votado é adversário. Gap de {gap_to_first:,} votos a superar.',
            })
        elif first_is_allied and first_candidate and not first_candidate.get('is_sorgatto'):
            recommendations.append({
                'priority': 'medium',
                'icon': 'handshake',
                'text': f'Deputado mais votado ({first_candidate["name"]}) é aliado. Buscar sinergia na campanha.',
            })

        return {
            'classification': classification,
            'classification_label': classification_labels[classification],
            'potential': potential,
            'structure': structure,
            'electoral_comparison': electoral_comparison,
            'activity': activity,
            'score': score_detail,
            'recommendations': recommendations,
        }

    def _build_allies(self, city):
        import math

        # 1. Deputados estaduais PL eleitos na cidade (exceto LS)
        dep_results = list(
            CandidateResult.objects.filter(
                election__election_type='state_deputy',
                election__year=2022,
                city=city,
                party='PL',
                is_elected=True,
            ).exclude(candidate_name='SORATTO').order_by('-votes')
        )

        # LS na cidade (dep estadual)
        ls_result = CandidateResult.objects.filter(
            election__election_type='state_deputy',
            election__year=2022,
            city=city,
            candidate_name='SORATTO',
        ).first()

        ls_votes = ls_result.votes if ls_result else 0
        ls_pct = float(ls_result.percentage) if ls_result else 0

        # Totais estaduais dos dep PL eleitos (uma única query)
        dep_names = [r.candidate_name for r in dep_results]
        state_totals = {}
        if dep_names:
            for row in CandidateResult.objects.filter(
                election__election_type='state_deputy',
                election__year=2022,
                candidate_name__in=dep_names,
                party='PL',
                is_elected=True,
            ).values('candidate_name').annotate(total=Sum('votes')):
                state_totals[row['candidate_name']] = row['total']

        # Deputados com dados
        deputies = []
        total_dep_pl_votes = 0
        for r in dep_results:
            total_dep_pl_votes += r.votes
            deputies.append({
                'name': r.candidate_name,
                'votes': r.votes,
                'pct': float(r.percentage),
                'total_state_votes': state_totals.get(r.candidate_name, 0),
            })

        # Deputado ponte sugerido (mais votado PL exceto LS)
        bridge_deputy = deputies[0]['name'] if deputies else None

        # 2. Jorginho Melo e Carol De Toni
        jm = CandidateResult.objects.filter(
            candidate_name='JORGINHO MELLO',
            election__election_type='governor',
            election__year=2022,
            city=city,
        ).first()
        ct = CandidateResult.objects.filter(
            candidate_name='CAROL DE TONI',
            election__election_type='federal_deputy',
            election__year=2022,
            city=city,
        ).first()

        jm_votes = jm.votes if jm else 0
        jm_pct = float(jm.percentage) if jm else 0
        ct_votes = ct.votes if ct else 0
        ct_pct = float(ct.percentage) if ct else 0

        # 3. Taxa de captura e gap
        capture_rate_jm = round(ls_votes / jm_votes * 100, 1) if jm_votes > 0 else 0
        capture_rate_dep = round(ls_votes / total_dep_pl_votes * 100, 1) if total_dep_pl_votes > 0 else 0
        gap_jm = jm_votes - ls_votes
        gap_dep = total_dep_pl_votes - ls_votes

        # 4. Cidades vizinhas com LS forte
        neighbors = []
        if city.geojson and 'coordinates' in city.geojson:
            geo = city.geojson
            ring = geo['coordinates'][0] if geo['type'] == 'Polygon' else geo['coordinates'][0][0]
            if ring:
                cx = sum(p[0] for p in ring) / len(ring)
                cy = sum(p[1] for p in ring) / len(ring)

                # Buscar cidades vizinhas com boa penetração
                nearby_cities = City.objects.select_related('region').exclude(
                    slug=city.slug
                ).exclude(geojson__isnull=True).exclude(votes_sorgatto_2022__isnull=True)

                for nc in nearby_cities:
                    ngeo = nc.geojson
                    if not ngeo or 'coordinates' not in ngeo:
                        continue
                    nring = ngeo['coordinates'][0] if ngeo['type'] == 'Polygon' else ngeo['coordinates'][0][0]
                    if not nring:
                        continue
                    ncx = sum(p[0] for p in nring) / len(nring)
                    ncy = sum(p[1] for p in nring) / len(nring)

                    dx = (cx - ncx) * 111 * math.cos(math.radians((cy + ncy) / 2))
                    dy = (cy - ncy) * 111
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist > 60:
                        continue

                    nvoters = nc.registered_voters or 0
                    nvotes = nc.votes_sorgatto_2022 or 0
                    npen = round(nvotes / nvoters * 100, 2) if nvoters > 0 else 0

                    neighbors.append({
                        'slug': nc.slug,
                        'name': nc.name,
                        'region': nc.region.name,
                        'distance_km': round(dist, 1),
                        'votes_ls': nvotes,
                        'penetration': npen,
                        'voters': nvoters,
                    })

                neighbors.sort(key=lambda n: n['penetration'], reverse=True)
                neighbors = neighbors[:5]

        # 5. Resumo acionável
        voters = city.registered_voters or 0
        potential_votes = round(capture_rate_jm / 100 * 0.5 * jm_votes) if jm_votes > 0 else 0
        # Estimar potencial: se capturasse 10% do gap com Jorginho
        potential_from_gap = round(gap_jm * 0.10) if gap_jm > 0 else 0

        # Penetração média estadual
        state_totals = City.objects.aggregate(
            total_votes=Sum('votes_sorgatto_2022'),
            total_voters=Sum('registered_voters'),
        )
        avg_penetration = round(
            (state_totals['total_votes'] or 0) / max(state_totals['total_voters'] or 1, 1) * 100, 2
        )

        return {
            'deputies': deputies,
            'ls_votes': ls_votes,
            'ls_pct': ls_pct,
            'total_dep_pl_votes': total_dep_pl_votes,
            'bridge_deputy': bridge_deputy,
            'jorginho': {'votes': jm_votes, 'pct': jm_pct},
            'carol': {'votes': ct_votes, 'pct': ct_pct},
            'capture_rate_jm': capture_rate_jm,
            'capture_rate_dep': capture_rate_dep,
            'gap_jm': gap_jm,
            'gap_dep': gap_dep,
            'neighbors': neighbors,
            'potential_from_gap': potential_from_gap,
            'avg_penetration': avg_penetration,
        }


ALLIED_PARTIES = {'PL', 'PP', 'REPUBLICANOS', 'UNIÃO', 'UNIÃO BRASIL'}
ADVERSARY_PARTIES = {'PT', 'PSOL', 'PCdoB', 'REDE', 'PV', 'SOLIDARIEDADE'}


class StrategicAnalysisAPI(APIView):
    """Análise estratégica: cidades aliadas vs adversárias."""

    def get(self, request):
        cities = (
            City.objects
            .select_related('region', 'region__macro_region')
            .annotate(
                total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
            )
            .order_by('region__name', 'name')
        )

        # Média estadual de penetração
        totals = City.objects.aggregate(
            total_votes=Sum('votes_sorgatto_2022'),
            total_voters=Sum('registered_voters'),
        )
        avg_penetration = 0
        if totals['total_voters']:
            avg_penetration = (totals['total_votes'] or 0) / totals['total_voters'] * 100

        result = []
        summary = {'base_forte': 0, 'potencial_oculto': 0, 'aliado_fraco': 0, 'territorio_hostil': 0, 'neutro': 0}

        for city in cities:
            voters = city.registered_voters or 0
            votes = city.votes_sorgatto_2022 or 0
            penetration = (votes / voters * 100) if voters > 0 else 0
            mayor_party = (city.mayor_party or '').upper().strip()

            # Classificação do alinhamento
            if mayor_party in ALLIED_PARTIES:
                alignment = 'allied'
            elif mayor_party in ADVERSARY_PARTIES:
                alignment = 'adversary'
            else:
                alignment = 'neutral'

            # Classificação do desempenho
            good_performance = penetration >= avg_penetration

            # Classificação final
            if alignment == 'allied' and good_performance:
                classification = 'base_forte'
            elif alignment == 'adversary' and good_performance:
                classification = 'potencial_oculto'
            elif alignment == 'allied' and not good_performance:
                classification = 'aliado_fraco'
            elif alignment == 'adversary' and not good_performance:
                classification = 'territorio_hostil'
            else:
                # Neutro: classificar pelo desempenho
                classification = 'potencial_oculto' if good_performance else 'neutro'

            # Score composto (0-100)
            align_score = {'allied': 100, 'neutral': 50, 'adversary': 0}[alignment]
            vereadores_pct = (city.num_vereadores_pl / city.num_vereadores * 100) if city.num_vereadores else 0
            pen_normalized = min(penetration / max(avg_penetration * 2, 0.01) * 100, 100)
            has_structure = 100 if city.pl_executive_president else 0

            score = round(
                align_score * 0.30
                + vereadores_pct * 0.20
                + pen_normalized * 0.35
                + has_structure * 0.15
            )

            summary[classification] = summary.get(classification, 0) + 1

            result.append({
                'slug': city.slug,
                'name': city.name,
                'region_name': city.region.name,
                'region_slug': city.region.slug,
                'macro_region': city.region.macro_region.name,
                'population': city.population,
                'registered_voters': voters,
                'mayor_name': city.mayor_name or '',
                'mayor_party': city.mayor_party or '',
                'num_vereadores': city.num_vereadores or 0,
                'num_vereadores_pl': city.num_vereadores_pl or 0,
                'pl_executive_president': city.pl_executive_president or '',
                'votes_2022': votes,
                'penetration': round(penetration, 2),
                'classification': classification,
                'alignment': alignment,
                'score': score,
                'contacts': city.total_contacts,
            })

        return Response({
            'avg_penetration': round(avg_penetration, 2),
            'summary': summary,
            'cities': result,
        })


class ZoneRankingAPI(APIView):
    """Ranking de zonas eleitorais por desempenho do LS."""

    def get(self, request):
        from apps.elections.models import ZoneResult

        # Buscar todos os resultados por zona (deputado federal 2022)
        zone_qs = (
            ZoneResult.objects
            .filter(election__year=2022, election__election_type='federal_deputy')
            .select_related('city', 'city__region')
            .order_by('zone_number', '-votes')
        )

        # Agrupar por zona, deduplicar (city+candidate)
        zones_raw = {}
        seen = set()
        for zr in zone_qs:
            key = (zr.zone_number, zr.city_id, zr.candidate_name)
            if key in seen:
                continue
            seen.add(key)

            zn = zr.zone_number
            if zn not in zones_raw:
                zones_raw[zn] = {
                    'zone_number': zn,
                    'candidates': {},
                    'cities': {},
                    'ls_votes': 0,
                    'total_votes': 0,
                }
            z = zones_raw[zn]

            # Acumular votos por candidato
            cand_key = (zr.candidate_name, zr.party)
            if cand_key not in z['candidates']:
                z['candidates'][cand_key] = {
                    'name': zr.candidate_name,
                    'party': zr.party,
                    'votes': 0,
                    'is_sorgatto': zr.is_sorgatto,
                }
            z['candidates'][cand_key]['votes'] += zr.votes
            z['total_votes'] += zr.votes

            if zr.is_sorgatto:
                z['ls_votes'] += zr.votes

            # Cidades da zona
            if zr.city_id not in z['cities']:
                z['cities'][zr.city_id] = {
                    'slug': zr.city.slug,
                    'name': zr.city.name,
                    'region': zr.city.region.name if zr.city.region else '',
                    'region_slug': zr.city.region.slug if zr.city.region else '',
                }

        # Processar zonas
        result = []
        for zn, z in zones_raw.items():
            candidates = sorted(z['candidates'].values(), key=lambda c: c['votes'], reverse=True)
            ls_cand = next((c for c in candidates if c['is_sorgatto']), None)

            # Posição do LS
            ls_position = 0
            if ls_cand:
                for i, c in enumerate(candidates, 1):
                    if c['is_sorgatto']:
                        ls_position = i
                        break

            ls_pct = round(z['ls_votes'] / max(z['total_votes'], 1) * 100, 2)

            # Top competitor (não LS)
            top_competitor = next((c for c in candidates if not c['is_sorgatto']), None)

            # Gap
            gap_to_first = 0
            if candidates and ls_cand and not candidates[0]['is_sorgatto']:
                gap_to_first = candidates[0]['votes'] - ls_cand['votes']

            cities_list = sorted(z['cities'].values(), key=lambda c: c['name'])

            # Classificação de performance
            if ls_position == 1:
                performance = 'lider'
            elif ls_position <= 3:
                performance = 'competitivo'
            elif ls_position <= 5:
                performance = 'medio'
            elif ls_cand:
                performance = 'baixo'
            else:
                performance = 'ausente'

            result.append({
                'zone_number': zn,
                'cities': cities_list,
                'city_slugs': [c['slug'] for c in cities_list],
                'city_names': ', '.join(c['name'] for c in cities_list),
                'region': cities_list[0]['region'] if cities_list else '',
                'ls_votes': z['ls_votes'],
                'ls_position': ls_position,
                'ls_percentage': ls_pct,
                'total_votes': z['total_votes'],
                'total_candidates': len(candidates),
                'top_competitor': {
                    'name': top_competitor['name'],
                    'party': top_competitor['party'],
                    'votes': top_competitor['votes'],
                } if top_competitor else None,
                'gap_to_first': gap_to_first,
                'performance': performance,
                'top_5': [
                    {
                        'name': c['name'],
                        'party': c['party'],
                        'votes': c['votes'],
                        'is_sorgatto': c['is_sorgatto'],
                    }
                    for c in candidates[:5]
                ],
            })

        # Ordenar por votos LS desc
        result.sort(key=lambda z: z['ls_votes'], reverse=True)

        # Adicionar ranking
        for i, z in enumerate(result, 1):
            z['ranking'] = i

        # Criar mapa city_slug -> zone performance para colorir mapa
        city_zone_map = {}
        for z in result:
            for slug in z['city_slugs']:
                # Se cidade já está em outra zona, manter a melhor performance
                if slug not in city_zone_map or z['ls_position'] < city_zone_map[slug]['ls_position']:
                    city_zone_map[slug] = {
                        'zone_number': z['zone_number'],
                        'ls_votes': z['ls_votes'],
                        'ls_position': z['ls_position'],
                        'ls_percentage': z['ls_percentage'],
                        'performance': z['performance'],
                    }

        # Resumo
        summary = {'lider': 0, 'competitivo': 0, 'medio': 0, 'baixo': 0, 'ausente': 0}
        for z in result:
            summary[z['performance']] = summary.get(z['performance'], 0) + 1

        return Response({
            'total_zones': len(result),
            'summary': summary,
            'zones': result,
            'city_zone_map': city_zone_map,
        })


class VoteTransferAPI(APIView):
    """Transferência de votos: identifica oportunidades de expansão entre cidades vizinhas."""

    def get(self, request):
        import math

        cities = (
            City.objects
            .select_related('region')
            .exclude(geojson__isnull=True)
            .order_by('name')
        )

        # Votos de aliados por cidade
        jorginho_votes = {}
        carol_votes = {}
        jorginho_qs = CandidateResult.objects.filter(
            candidate_name='JORGINHO MELLO',
            election__election_type='governor',
            election__year=2022,
        ).values('city__slug', 'votes', 'percentage')
        for r in jorginho_qs:
            jorginho_votes[r['city__slug']] = {
                'votes': r['votes'],
                'pct': float(r['percentage']),
            }

        carol_qs = CandidateResult.objects.filter(
            candidate_name='CAROL DE TONI',
            election__election_type='federal_deputy',
            election__year=2022,
        ).values('city__slug', 'votes', 'percentage')
        for r in carol_qs:
            carol_votes[r['city__slug']] = {
                'votes': r['votes'],
                'pct': float(r['percentage']),
            }

        # Calcular centroide e penetração de cada cidade
        city_data = {}
        for city in cities:
            geo = city.geojson
            if not geo or 'coordinates' not in geo:
                continue
            coords = geo['coordinates']
            ring = coords[0] if geo['type'] == 'Polygon' else coords[0][0]
            if not ring:
                continue
            cx = sum(p[0] for p in ring) / len(ring)
            cy = sum(p[1] for p in ring) / len(ring)

            voters = city.registered_voters or 0
            votes = city.votes_sorgatto_2022 or 0
            penetration = (votes / voters * 100) if voters > 0 else 0

            jm = jorginho_votes.get(city.slug, {'votes': 0, 'pct': 0})
            ct = carol_votes.get(city.slug, {'votes': 0, 'pct': 0})

            city_data[city.slug] = {
                'slug': city.slug,
                'name': city.name,
                'region_name': city.region.name,
                'region_slug': city.region.slug,
                'cx': cx,
                'cy': cy,
                'voters': voters,
                'votes': votes,
                'penetration': round(penetration, 2),
                'meta': city.meta_votes or 0,
                'population': city.population or 0,
                'jorginho_votes': jm['votes'],
                'jorginho_pct': round(jm['pct'], 1),
                'carol_votes': ct['votes'],
                'carol_pct': round(ct['pct'], 1),
            }

        # Médias estaduais
        all_pens = [c['penetration'] for c in city_data.values() if c['voters'] > 0]
        avg_pen = sum(all_pens) / len(all_pens) if all_pens else 0
        all_jm_pcts = [c['jorginho_pct'] for c in city_data.values() if c['jorginho_pct'] > 0]
        avg_jm = sum(all_jm_pcts) / len(all_jm_pcts) if all_jm_pcts else 0
        all_ct_pcts = [c['carol_pct'] for c in city_data.values() if c['carol_pct'] > 0]
        avg_ct = sum(all_ct_pcts) / len(all_ct_pcts) if all_ct_pcts else 0

        # Distância haversine simplificada (km)
        def dist_km(c1, c2):
            dx = (c1['cx'] - c2['cx']) * 111 * math.cos(math.radians((c1['cy'] + c2['cy']) / 2))
            dy = (c1['cy'] - c2['cy']) * 111
            return math.sqrt(dx * dx + dy * dy)

        # Encontrar oportunidades LS: cidade forte → cidade fraca vizinha
        MAX_DIST = 50
        MIN_SOURCE_PEN = avg_pen
        opportunities = []
        slugs = list(city_data.keys())

        for src_slug in slugs:
            src = city_data[src_slug]
            if src['penetration'] < MIN_SOURCE_PEN or src['voters'] < 100:
                continue
            for tgt_slug in slugs:
                if src_slug == tgt_slug:
                    continue
                tgt = city_data[tgt_slug]
                if tgt['penetration'] >= src['penetration'] or tgt['voters'] < 100:
                    continue
                d = dist_km(src, tgt)
                if d > MAX_DIST:
                    continue
                pen_diff = src['penetration'] - tgt['penetration']
                potential_votes = round(pen_diff / 100 * tgt['voters'])
                if potential_votes < 10:
                    continue
                proximity_factor = max(0, 1 - d / MAX_DIST)
                score = round(min(
                    (pen_diff * 10) * 0.4 +
                    (potential_votes / 50) * 0.3 +
                    proximity_factor * 100 * 0.3,
                    100
                ))
                opportunities.append({
                    'source': {
                        'slug': src['slug'], 'name': src['name'],
                        'region': src['region_name'],
                        'penetration': src['penetration'], 'votes': src['votes'],
                        'cx': src['cx'], 'cy': src['cy'],
                    },
                    'target': {
                        'slug': tgt['slug'], 'name': tgt['name'],
                        'region': tgt['region_name'],
                        'penetration': tgt['penetration'], 'votes': tgt['votes'],
                        'voters': tgt['voters'],
                        'cx': tgt['cx'], 'cy': tgt['cy'],
                    },
                    'distance_km': round(d, 1),
                    'pen_diff': round(pen_diff, 2),
                    'potential_votes': potential_votes,
                    'score': score,
                })

        opportunities.sort(key=lambda o: o['score'], reverse=True)
        opportunities = opportunities[:200]
        for opp in opportunities:
            opp['priority'] = 'alta' if opp['score'] >= 60 else ('media' if opp['score'] >= 30 else 'baixa')

        summary = {'alta': 0, 'media': 0, 'baixa': 0}
        for opp in opportunities:
            summary[opp['priority']] += 1

        # Classificar cidades com cruzamento de aliados
        cities_list = []
        opp_summary = {'zona_ouro': 0, 'buscar_jorginho': 0, 'buscar_carol': 0, 'buscar_ambos': 0, 'polo_ls': 0, 'baixa_prioridade': 0}

        for c in city_data.values():
            ls_forte = c['penetration'] >= avg_pen
            jm_forte = c['jorginho_pct'] >= avg_jm
            ct_forte = c['carol_pct'] >= avg_ct

            if c['penetration'] >= avg_pen * 1.5:
                level = 'polo'
            elif ls_forte:
                level = 'acima'
            elif c['penetration'] > 0:
                level = 'abaixo'
            else:
                level = 'zero'

            # Classificação cruzada
            if ls_forte and jm_forte and ct_forte:
                opp_class = 'zona_ouro'
            elif not ls_forte and jm_forte and ct_forte:
                opp_class = 'buscar_ambos'
            elif not ls_forte and jm_forte:
                opp_class = 'buscar_jorginho'
            elif not ls_forte and ct_forte:
                opp_class = 'buscar_carol'
            elif ls_forte:
                opp_class = 'polo_ls'
            else:
                opp_class = 'baixa_prioridade'

            opp_summary[opp_class] += 1
            cities_list.append({**c, 'level': level, 'opp_class': opp_class})

        level_summary = {'polo': 0, 'acima': 0, 'abaixo': 0, 'zero': 0}
        for c in cities_list:
            level_summary[c['level']] += 1

        return Response({
            'avg_penetration': round(avg_pen, 2),
            'avg_jorginho': round(avg_jm, 1),
            'avg_carol': round(avg_ct, 1),
            'total_opportunities': len(opportunities),
            'total_potential_votes': sum(o['potential_votes'] for o in opportunities),
            'summary': summary,
            'level_summary': level_summary,
            'opp_summary': opp_summary,
            'opportunities': opportunities,
            'cities': cities_list,
        })


class NeighborDeputiesAPI(APIView):
    """Deputados estaduais PL aliados: mapeia influência por cidade e oportunidades de articulação."""

    def get(self, request):
        cities = City.objects.select_related('region').order_by('name')

        # Todos dep. estaduais PL eleitos 2022 (excluindo LS)
        dep_results = CandidateResult.objects.filter(
            election__election_type='state_deputy',
            election__year=2022,
            party='PL',
            is_elected=True,
        ).exclude(
            candidate_name='SORATTO',
        ).values('candidate_name', 'city__slug', 'votes', 'percentage')

        # Votos LS por cidade (dep. estadual)
        ls_results = CandidateResult.objects.filter(
            election__election_type='state_deputy',
            election__year=2022,
            candidate_name='SORATTO',
        ).values('city__slug', 'votes', 'percentage')

        ls_by_city = {}
        for r in ls_results:
            ls_by_city[r['city__slug']] = {
                'votes': r['votes'],
                'pct': float(r['percentage']),
            }

        # Estrutura: {deputado: {slug: {votes, pct}}}
        dep_names = set()
        dep_by_city = {}  # {slug: [{name, votes, pct}, ...]}
        for r in dep_results:
            name = r['candidate_name']
            slug = r['city__slug']
            dep_names.add(name)
            if slug not in dep_by_city:
                dep_by_city[slug] = []
            dep_by_city[slug].append({
                'name': name,
                'votes': r['votes'],
                'pct': float(r['percentage']),
            })

        # Totais por deputado
        dep_totals = {}
        for slug, deps in dep_by_city.items():
            for d in deps:
                if d['name'] not in dep_totals:
                    dep_totals[d['name']] = {'total_votes': 0, 'cities_with_votes': 0}
                dep_totals[d['name']]['total_votes'] += d['votes']
                if d['votes'] > 0:
                    dep_totals[d['name']]['cities_with_votes'] += 1

        # Montar lista de deputados
        deputies_list = []
        for name in sorted(dep_names):
            t = dep_totals.get(name, {'total_votes': 0, 'cities_with_votes': 0})
            deputies_list.append({
                'name': name,
                'total_votes': t['total_votes'],
                'cities_with_votes': t['cities_with_votes'],
            })
        deputies_list.sort(key=lambda d: d['total_votes'], reverse=True)

        # Por cidade: dep mais votado, classificação de oportunidade
        cities_list = []
        classification_summary = {
            'ponte_forte': 0,      # dep forte + LS fraco → articular com dep
            'base_conjunta': 0,    # dep forte + LS forte → consolidar
            'territorio_dep': 0,   # dep forte + LS zero → dep como porta de entrada
            'territorio_ls': 0,    # dep fraco + LS forte → LS domina sozinho
            'sem_presenca': 0,     # ambos fracos
        }

        # Médias para classificação
        ls_pcts = [v['pct'] for v in ls_by_city.values() if v['pct'] > 0]
        avg_ls = sum(ls_pcts) / len(ls_pcts) if ls_pcts else 0

        for city in cities:
            ls = ls_by_city.get(city.slug, {'votes': 0, 'pct': 0})
            deps = dep_by_city.get(city.slug, [])

            # Deputado mais votado na cidade (exceto LS)
            best_dep = None
            if deps:
                deps_sorted = sorted(deps, key=lambda d: d['votes'], reverse=True)
                best_dep = deps_sorted[0]

            # Top 3 deputados
            top3 = sorted(deps, key=lambda d: d['votes'], reverse=True)[:3] if deps else []

            best_dep_pct = best_dep['pct'] if best_dep else 0
            ls_forte = ls['pct'] >= avg_ls
            dep_forte = best_dep_pct >= 2.0  # dep com pelo menos 2% na cidade

            if dep_forte and not ls_forte and ls['pct'] > 0:
                classification = 'ponte_forte'
            elif dep_forte and ls_forte:
                classification = 'base_conjunta'
            elif dep_forte and ls['pct'] == 0:
                classification = 'territorio_dep'
            elif not dep_forte and ls_forte:
                classification = 'territorio_ls'
            else:
                classification = 'sem_presenca'

            classification_summary[classification] += 1

            cities_list.append({
                'slug': city.slug,
                'name': city.name,
                'region_name': city.region.name,
                'region_slug': city.region.slug,
                'ls_votes': ls['votes'],
                'ls_pct': ls['pct'],
                'best_dep_name': best_dep['name'] if best_dep else None,
                'best_dep_votes': best_dep['votes'] if best_dep else 0,
                'best_dep_pct': best_dep['pct'] if best_dep else 0,
                'top3_deps': top3,
                'total_dep_votes': sum(d['votes'] for d in deps),
                'classification': classification,
            })

        return Response({
            'avg_ls': round(avg_ls, 2),
            'deputies': deputies_list,
            'summary': classification_summary,
            'cities': cities_list,
        })


class PLNetworkAPI(APIView):
    """Força da rede PL: mede a presença e estrutura do PL em cada cidade."""

    def get(self, request):
        cities = (
            City.objects
            .select_related('region', 'region__macro_region')
            .annotate(
                total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
                coord_count=Count('contacts', filter=Q(
                    contacts__is_active=True,
                    contacts__category__in=['coordenador_regional', 'coordenador_municipal'],
                )),
                avg_engagement=models.Avg('contacts__engagement_level', filter=Q(contacts__is_active=True)),
            )
            .order_by('region__name', 'name')
        )

        # Referência estadual: máxima densidade de contatos para normalizar
        totals = City.objects.aggregate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
            total_voters=Sum('registered_voters'),
        )
        state_density = 0
        if totals['total_voters']:
            state_density = (totals['total_contacts'] or 0) / totals['total_voters'] * 100

        result = []
        levels = {'forte': 0, 'moderada': 0, 'fraca': 0, 'ausente': 0}

        for city in cities:
            voters = city.registered_voters or 0

            # 1. Coordenador (25%) — tem coordenador = 100, senão 0
            coord_score = 100 if (city.coord_count or 0) > 0 else 0

            # 2. Vereadores PL (25%) — proporção
            ver_pct = (city.num_vereadores_pl / city.num_vereadores * 100) if city.num_vereadores else 0
            ver_score = min(ver_pct * 2, 100)  # 50% dos vereadores = score 100

            # 3. Diretório PL (20%) — tem presidente = 100
            dir_score = 100 if city.pl_executive_president else 0

            # 4. Contatos ativos (15%) — densidade normalizada
            density = ((city.total_contacts or 0) / max(voters, 1)) * 100
            # Normalizar: 2x a média estadual = 100
            contact_score = min(density / max(state_density * 2, 0.01) * 100, 100)

            # 5. Engajamento médio (15%) — escala 1-5, normalizar para 0-100
            avg_eng = city.avg_engagement or 1
            eng_score = (avg_eng - 1) / 4 * 100  # 1→0, 5→100

            # Score total ponderado
            total_score = round(
                coord_score * 0.25
                + ver_score * 0.25
                + dir_score * 0.20
                + contact_score * 0.15
                + eng_score * 0.15
            )

            # Classificar nível
            if total_score >= 60:
                level = 'forte'
            elif total_score >= 35:
                level = 'moderada'
            elif total_score > 0:
                level = 'fraca'
            else:
                level = 'ausente'

            levels[level] = levels.get(level, 0) + 1

            result.append({
                'slug': city.slug,
                'name': city.name,
                'region_name': city.region.name,
                'region_slug': city.region.slug,
                'population': city.population,
                'registered_voters': voters,
                'mayor_name': city.mayor_name or '',
                'mayor_party': city.mayor_party or '',
                'num_vereadores': city.num_vereadores or 0,
                'num_vereadores_pl': city.num_vereadores_pl or 0,
                'pl_executive_president': city.pl_executive_president or '',
                'has_coordinator': (city.coord_count or 0) > 0,
                'coordinator_count': city.coord_count or 0,
                'contacts': city.total_contacts or 0,
                'avg_engagement': round(avg_eng, 1),
                'score': total_score,
                'level': level,
                'components': {
                    'coordinator': round(coord_score),
                    'vereadores': round(ver_score),
                    'directory': round(dir_score),
                    'contacts': round(contact_score),
                    'engagement': round(eng_score),
                },
            })

        return Response({
            'state_density': round(state_density, 2),
            'summary': levels,
            'cities': result,
        })


class Elections2022API(APIView):
    """Resultados eleitorais 2022 — visão geral para o mapa."""

    def get(self, request):
        from collections import defaultdict

        # Posição do LS em cada cidade (dep. federal)
        dep_results = (
            CandidateResult.objects.filter(
                election__election_type='federal_deputy',
                election__year=2022,
            )
            .values('city__slug', 'city__name', 'city__region__name', 'city__region__slug',
                    'city__registered_voters', 'candidate_name', 'votes', 'percentage', 'is_sorgatto', 'is_elected', 'party')
            .order_by('city__slug', '-votes')
        )

        # Agrupar por cidade
        city_candidates = defaultdict(list)
        for r in dep_results:
            city_candidates[r['city__slug']].append(r)

        cities = []
        total_ls_votes = 0
        positions = []
        perf_counts = {'top3': 0, 'top5': 0, 'top10': 0, 'below': 0}

        for slug, candidates in city_candidates.items():
            ls_pos = None
            ls_votes = 0
            ls_pct = 0
            first_name = candidates[0]['candidate_name'] if candidates else ''
            first_votes = candidates[0]['votes'] if candidates else 0

            for i, c in enumerate(candidates, 1):
                if c['is_sorgatto']:
                    ls_pos = i
                    ls_votes = c['votes']
                    ls_pct = float(c['percentage'])
                    break

            if ls_pos is None:
                continue

            total_ls_votes += ls_votes
            positions.append(ls_pos)

            if ls_pos <= 3:
                perf_counts['top3'] += 1
            elif ls_pos <= 5:
                perf_counts['top5'] += 1
            elif ls_pos <= 10:
                perf_counts['top10'] += 1
            else:
                perf_counts['below'] += 1

            # Classificação de performance
            if ls_pos == 1:
                perf = 'primeiro'
            elif ls_pos <= 3:
                perf = 'top3'
            elif ls_pos <= 5:
                perf = 'top5'
            elif ls_pos <= 10:
                perf = 'top10'
            else:
                perf = 'abaixo'

            info = candidates[0]
            cities.append({
                'slug': slug,
                'name': info['city__name'],
                'region': info['city__region__name'],
                'region_slug': info['city__region__slug'],
                'voters': info['city__registered_voters'] or 0,
                'ls_votes': ls_votes,
                'ls_position': ls_pos,
                'ls_pct': ls_pct,
                'total_candidates': len(candidates),
                'first_name': first_name,
                'first_votes': first_votes,
                'performance': perf,
            })

        cities.sort(key=lambda c: c['ls_position'])

        # Zonas — resumo
        zone_agg = (
            ZoneResult.objects.filter(
                election__election_type='federal_deputy',
                election__year=2022,
                is_sorgatto=True,
            )
            .values('zone_number')
            .annotate(total_votes=Sum('votes'))
            .order_by('-total_votes')
        )
        zones = [
            {'zone_number': z['zone_number'], 'votes': z['total_votes']}
            for z in zone_agg
        ]

        avg_pos = round(sum(positions) / len(positions), 1) if positions else 0

        return Response({
            'summary': {
                'total_cities': len(cities),
                'total_ls_votes': total_ls_votes,
                'avg_position': avg_pos,
                'top3': perf_counts['top3'],
                'top5': perf_counts['top5'],
                'top10': perf_counts['top10'],
                'below': perf_counts['below'],
                'total_zones': len(zones),
            },
            'perf_summary': {
                'primeiro': sum(1 for c in cities if c['performance'] == 'primeiro'),
                'top3': sum(1 for c in cities if c['performance'] == 'top3'),
                'top5': sum(1 for c in cities if c['performance'] == 'top5'),
                'top10': sum(1 for c in cities if c['performance'] == 'top10'),
                'abaixo': sum(1 for c in cities if c['performance'] == 'abaixo'),
            },
            'cities': cities,
            'zones': zones,
        })


@login_required
def dashboard_home(request):
    return render(request, 'dashboard/index.html')


@login_required
def map_region_view(request, slug):
    return render(request, 'maps/region.html', {'region_slug': slug})


@login_required
def map_city_view(request, slug):
    return render(request, 'maps/city.html', {'city_slug': slug})
