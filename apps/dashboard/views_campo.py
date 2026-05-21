"""
Views para o PWA Campo (mobile para uso em campo).
Inclui views de template e endpoints de API.
"""
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.contacts.models import Contact, Interaction
from apps.campaigns.models import Task
from apps.events.models import Event
from apps.geography.models import City


# ====================================================
# Views de template (renderizam HTML)
# ====================================================

@login_required
def campo_home(request):
    return render(request, 'pwa/home.html')


@login_required
def campo_contato(request):
    return render(request, 'pwa/contato.html')


@login_required
def campo_interacao(request):
    return render(request, 'pwa/interacao.html')


@login_required
def campo_checkin(request):
    return render(request, 'pwa/checkin.html')


@login_required
def campo_cidade(request):
    return render(request, 'pwa/cidade.html')


# ====================================================
# API endpoints para o PWA
# ====================================================

def _territory(request):
    """Retorna filtro territorial do usuário logado."""
    return request.user.get_territory_filter()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campo_home_api(request):
    """KPIs e próximos eventos para a home do campo."""
    hoje = date.today()
    tf = _territory(request)

    # Filtro territorial para contatos/interações
    ct_filter = {}
    if 'city_id' in tf:
        ct_filter = {'city_id': tf['city_id']}
    elif 'region_id' in tf:
        ct_filter = {'region_id': tf['region_id']}

    ev_filter = {}
    if 'city_id' in tf:
        ev_filter = {'city_id': tf['city_id']}
    elif 'region_id' in tf:
        ev_filter = {'region_id': tf['region_id']}

    contatos_hoje = Contact.objects.filter(created_at__date=hoje, **ct_filter).count()
    interacoes_hoje = Interaction.objects.filter(created_at__date=hoje).count()
    demandas_pendentes = Task.objects.exclude(
        phase__in=['executed', 'completed']
    ).filter(**ev_filter).count()
    eventos_hoje = Event.objects.filter(date__date=hoje, **ev_filter).count()

    # Próximos 5 eventos
    proximos = Event.objects.filter(
        date__gte=hoje, **ev_filter
    ).select_related('city').order_by('date')[:5]

    eventos_list = [{
        'id': ev.id,
        'title': ev.title,
        'event_type_display': ev.get_event_type_display(),
        'date': ev.date.isoformat(),
        'city_name': ev.city.name if ev.city else '',
    } for ev in proximos]

    return Response({
        'stats': {
            'contatos_hoje': contatos_hoje,
            'interacoes_hoje': interacoes_hoje,
            'demandas_pendentes': demandas_pendentes,
            'eventos_hoje': eventos_hoje,
        },
        'proximos_eventos': eventos_list,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campo_cidades_api(request):
    """Lista de cidades para select ou busca."""
    search = request.query_params.get('search', '')
    tf = _territory(request)
    qs = City.objects.select_related('region').all()

    # Filtro territorial
    if 'city_id' in tf:
        qs = qs.filter(id=tf['city_id'])
    elif 'region_id' in tf:
        qs = qs.filter(region_id=tf['region_id'])

    if search:
        qs = qs.filter(name__icontains=search)

    cidades = [{
        'id': c.id,
        'name': c.name,
        'region_name': c.region.name if c.region else '',
    } for c in qs[:50]]

    return Response(cidades)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campo_cidade_detalhe_api(request, pk):
    """Detalhes completos de uma cidade (termômetro)."""
    try:
        c = City.objects.select_related('region').get(pk=pk)
    except City.DoesNotExist:
        return Response({'error': 'Cidade não encontrada'}, status=404)

    # Contatos na cidade
    contatos_qs = Contact.objects.filter(city=c, is_active=True)
    total_contatos = contatos_qs.count()
    apoiadores = contatos_qs.filter(
        category__in=['apoiador', 'coordenador_regional', 'coordenador_municipal', 'coordenador_bairro']
    ).count()
    liderancas = contatos_qs.filter(category='lideranca').count()

    # Penetração
    penetration = 0
    if c.registered_voters > 0:
        penetration = round((c.votes_sorgatto_2022 / c.registered_voters) * 100, 1)

    return Response({
        'id': c.id,
        'name': c.name,
        'region_name': c.region.name if c.region else '',
        'population': c.population,
        'registered_voters': c.registered_voters,
        'votes_sorgatto_2022': c.votes_sorgatto_2022,
        'penetration': penetration,
        'mayor_name': c.mayor_name,
        'mayor_party': c.mayor_party,
        'num_vereadores': c.num_vereadores,
        'num_vereadores_pl': c.num_vereadores_pl,
        'meta_votes': c.meta_votes,
        'total_contatos': total_contatos,
        'apoiadores': apoiadores,
        'liderancas': liderancas,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campo_cidade_por_gps_api(request):
    """Encontra a cidade mais próxima por coordenadas GPS.
    Usa uma busca simples pela menor diferença de coordenadas
    comparando com o centróide do GeoJSON de cada cidade.
    """
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')

    if not lat or not lng:
        return Response({'error': 'lat e lng são obrigatórios'}, status=400)

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response({'error': 'lat e lng devem ser números'}, status=400)

    # Busca simples: pegar todas as cidades com geojson e calcular distância
    # Para SC, são ~295 cidades, performance aceitável
    melhor_cidade = None
    melhor_dist = float('inf')

    for city in City.objects.select_related('region').all():
        if not city.geojson:
            continue

        # Centróide simples: média das coordenadas do bbox ou primeiro ponto
        try:
            geojson = city.geojson
            coords = _extrair_centroide(geojson)
            if coords:
                clng, clat = coords
                dist = (lat - clat) ** 2 + (lng - clng) ** 2
                if dist < melhor_dist:
                    melhor_dist = dist
                    melhor_cidade = city
        except Exception:
            continue

    if melhor_cidade:
        return Response({
            'id': melhor_cidade.id,
            'name': melhor_cidade.name,
            'region_name': melhor_cidade.region.name if melhor_cidade.region else '',
        })

    return Response({'error': 'Nenhuma cidade encontrada'}, status=404)


def _extrair_centroide(geojson):
    """Extrai um centróide aproximado do GeoJSON."""
    try:
        geo = geojson
        if isinstance(geo, str):
            import json
            geo = json.loads(geo)

        # Pode ser Feature ou Geometry
        if geo.get('type') == 'Feature':
            geo = geo['geometry']

        coords = geo.get('coordinates', [])
        if not coords:
            return None

        # Flatten all coordinates
        all_coords = []

        def flatten(c):
            if isinstance(c[0], (int, float)):
                all_coords.append(c)
            else:
                for item in c:
                    flatten(item)

        flatten(coords)

        if not all_coords:
            return None

        avg_lng = sum(c[0] for c in all_coords) / len(all_coords)
        avg_lat = sum(c[1] for c in all_coords) / len(all_coords)
        return (avg_lng, avg_lat)
    except Exception:
        return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campo_eventos_checkin_api(request):
    """Eventos disponíveis para check-in (hoje e próximos 3 dias)."""
    hoje = date.today()
    limite = hoje + timedelta(days=3)

    eventos = Event.objects.filter(
        date__date__gte=hoje,
        date__date__lte=limite,
    ).select_related('city').order_by('date')

    user = request.user
    result = []
    for ev in eventos:
        checked_in = ev.contacts_attended.filter(
            interactions__performed_by=user,
            interactions__interaction_type='event',
        ).exists()

        result.append({
            'id': ev.id,
            'title': ev.title,
            'event_type_display': ev.get_event_type_display(),
            'date': ev.date.isoformat(),
            'city_name': ev.city.name if ev.city else '',
            'expected_attendees': ev.expected_attendees,
            'checked_in': checked_in,
        })

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def campo_checkin_api(request, event_id):
    """Registra check-in do usuário em um evento."""
    try:
        evento = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Evento não encontrado'}, status=404)

    # Incrementar presença real
    evento.actual_attendees = (evento.actual_attendees or 0) + 1
    evento.save(update_fields=['actual_attendees'])

    return Response({'ok': True, 'actual_attendees': evento.actual_attendees})
