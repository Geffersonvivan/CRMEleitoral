from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.contacts.models import Contact
from apps.geography.models import Region

from .models import Donation, Expense, Captador
from .serializers import (
    DonationSerializer, ExpenseSerializer,
    CaptadorSerializer, CaptadorCreateSerializer,
    PublicDoacaoSerializer,
)


class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.select_related('donor', 'captador__contact').all()
    serializer_class = DonationSerializer
    filterset_fields = ['method', 'is_verified', 'pix_status', 'captador']


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    filterset_fields = ['category']


class CaptadorViewSet(viewsets.ModelViewSet):
    queryset = Captador.objects.select_related(
        'contact', 'contact__city', 'contact__region', 'coordenador__contact'
    ).all()
    serializer_class = CaptadorSerializer
    filterset_fields = ['tipo', 'is_active', 'coordenador']
    search_fields = ['contact__full_name', 'contact__cpf', 'slug']

    def get_serializer_class(self):
        if self.action == 'create':
            return CaptadorCreateSerializer
        return CaptadorSerializer

    def perform_create(self, serializer):
        captador = serializer.save()
        captador.generate_qrcode()

    @action(detail=True, methods=['post'])
    def qrcode(self, request, pk=None):
        captador = self.get_object()
        captador.generate_qrcode()
        return Response({'qrcode_url': captador.qrcode_image.url})

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        captador = self.get_object()
        doacoes = Donation.objects.filter(captador=captador, pix_status='paid')
        return Response({
            'total_doacoes': doacoes.count(),
            'total_arrecadado': doacoes.aggregate(t=Sum('amount'))['t'] or 0,
            'ultimas_doacoes': DonationSerializer(doacoes[:10], many=True).data,
        })


# ─── Endpoints Públicos (sem autenticação) ───────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def public_captador_info(request, slug):
    """Info pública do captador para a página de doação."""
    captador = get_object_or_404(Captador, slug=slug, is_active=True)
    return Response({
        'nome': captador.contact.full_name,
        'tipo': captador.get_tipo_display(),
        'foto_url': captador.contact.photo.url if captador.contact.photo else '',
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def public_criar_doacao(request, slug):
    """Criar doação a partir do formulário público."""
    captador = get_object_or_404(Captador, slug=slug, is_active=True)
    serializer = PublicDoacaoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Find-or-create Contact pelo CPF
    cpf = data['cpf']
    contact, _ = Contact.objects.get_or_create(
        cpf=cpf,
        defaults={
            'full_name': data['nome'],
            'phone': data.get('telefone', ''),
            'whatsapp': data.get('telefone', ''),
            'category': 'eleitor',
            'engagement_level': 2,
        }
    )

    # Criar doação
    donation = Donation.objects.create(
        donor=contact,
        amount=data['valor'],
        date=timezone.localdate(),
        method=Donation.Method.ONLINE,
        captador=captador,
        donor_cpf=cpf,
        donor_name=data['nome'],
        donor_phone=data.get('telefone', ''),
        pix_status='pending',
    )
    donation.calcular_comissoes()
    donation.save()

    return Response({
        'id': donation.id,
        'valor': str(donation.amount),
        'status': 'pending',
        'mensagem': 'Doação registrada com sucesso!',
    }, status=201)


# ─── Endpoint do Mapa de Doações ─────────────────────────────────────

def _filtrar_por_periodo(qs, periodo):
    """Aplica filtro de período ao queryset de doações."""
    if periodo == '7d':
        return qs.filter(date__gte=timezone.localdate() - timedelta(days=7))
    elif periodo == '30d':
        return qs.filter(date__gte=timezone.localdate() - timedelta(days=30))
    return qs


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doacoes_map_data(request):
    """Dados de doações agregados por região e cidade para colorir o mapa."""
    periodo = request.query_params.get('periodo', 'total')

    base_qs = Donation.objects.filter(captador__isnull=False)
    paid_qs = base_qs.filter(
        Q(pix_status='paid') | Q(is_verified=True)
    )
    paid_qs = _filtrar_por_periodo(paid_qs, periodo)

    # Agregação por região (baseado na região do captador)
    regions_qs = paid_qs.values(
        slug=models_F('captador__contact__region__slug'),
        name=models_F('captador__contact__region__name'),
    ).annotate(
        total=Sum('amount'),
        count=Count('id'),
        doadores=Count('donor_cpf', distinct=True),
        captadores=Count('captador', distinct=True),
    ).filter(slug__isnull=False)

    regions = {}
    for r in regions_qs:
        # Top captadores da região
        top = (paid_qs
               .filter(captador__contact__region__slug=r['slug'])
               .values(nome=models_F('captador__contact__full_name'))
               .annotate(total=Sum('amount'))
               .order_by('-total')[:3])
        regions[r['slug']] = {
            'name': r['name'],
            'total': float(r['total'] or 0),
            'count': r['count'],
            'doadores': r['doadores'],
            'captadores': r['captadores'],
            'top_captadores': list(top),
        }

    # Agregação por cidade (baseado na cidade do captador)
    cities_qs = paid_qs.values(
        slug=models_F('captador__contact__city__slug'),
        name=models_F('captador__contact__city__name'),
    ).annotate(
        total=Sum('amount'),
        count=Count('id'),
        doadores=Count('donor_cpf', distinct=True),
    ).filter(slug__isnull=False)

    cities = {}
    for c in cities_qs:
        cities[c['slug']] = {
            'name': c['name'],
            'total': float(c['total'] or 0),
            'count': c['count'],
            'doadores': c['doadores'],
        }

    # Totais gerais
    totals = paid_qs.aggregate(
        total=Sum('amount'),
        count=Count('id'),
        doadores=Count('donor_cpf', distinct=True),
        captadores=Count('captador', distinct=True),
    )

    return Response({
        'regions': regions,
        'cities': cities,
        'totals': {
            'total': float(totals['total'] or 0),
            'count': totals['count'],
            'doadores': totals['doadores'],
            'captadores': totals['captadores'],
        },
    })


def models_F(field):
    """Shortcut para django.db.models.F."""
    from django.db.models import F
    return F(field)


# ─── Drill-down: detalhes de doações por região ──────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doacoes_region_detail(request, slug):
    """Detalhamento de doações de uma região: coordenadores, apoiadores, cidades."""
    region = get_object_or_404(Region, slug=slug)
    periodo = request.query_params.get('periodo', 'total')

    paid_qs = Donation.objects.filter(
        captador__isnull=False,
        captador__contact__region=region,
    ).filter(Q(pix_status='paid') | Q(is_verified=True))
    paid_qs = _filtrar_por_periodo(paid_qs, periodo)

    # Totais da região
    totals = paid_qs.aggregate(
        total=Sum('amount'),
        count=Count('id'),
        doadores=Count('donor_cpf', distinct=True),
        captadores=Count('captador', distinct=True),
    )

    # Coordenadores da região com seus números
    coordenadores = []
    coords_qs = Captador.objects.filter(
        tipo='coordenador',
        contact__region=region,
        is_active=True,
    ).select_related('contact', 'contact__city')

    for coord in coords_qs:
        # Doações do coordenador (diretamente dele + dos seus apoiadores)
        apoiador_ids = list(coord.apoiadores.values_list('id', flat=True)) + [coord.id]
        coord_doacoes = paid_qs.filter(captador_id__in=apoiador_ids)
        coord_totals = coord_doacoes.aggregate(
            total=Sum('amount'), count=Count('id'),
        )

        # Apoiadores do coordenador
        apoiadores_list = []
        for ap in coord.apoiadores.filter(is_active=True).select_related('contact'):
            ap_doacoes = paid_qs.filter(captador=ap)
            ap_totals = ap_doacoes.aggregate(
                total=Sum('amount'), count=Count('id'),
            )
            apoiadores_list.append({
                'id': ap.id,
                'nome': ap.contact.full_name,
                'cidade': ap.contact.city.name if ap.contact.city else '',
                'total': float(ap_totals['total'] or 0),
                'count': ap_totals['count'],
            })

        coordenadores.append({
            'id': coord.id,
            'nome': coord.contact.full_name,
            'cidade': coord.contact.city.name if coord.contact.city else '',
            'apoiadores_count': len(apoiadores_list),
            'total': float(coord_totals['total'] or 0),
            'count': coord_totals['count'],
            'apoiadores': apoiadores_list,
        })

    coordenadores.sort(key=lambda x: x['total'], reverse=True)

    # Doações por cidade
    cidades = list(
        paid_qs
        .values(
            cidade_slug=models_F('captador__contact__city__slug'),
            cidade_nome=models_F('captador__contact__city__name'),
        )
        .annotate(
            total=Sum('amount'),
            count=Count('id'),
            doadores=Count('donor_cpf', distinct=True),
            captadores=Count('captador', distinct=True),
        )
        .filter(cidade_slug__isnull=False)
        .order_by('-total')
    )

    for c in cidades:
        c['total'] = float(c['total'] or 0)

    return Response({
        'region': {'slug': region.slug, 'name': region.name},
        'totals': {
            'total': float(totals['total'] or 0),
            'count': totals['count'],
            'doadores': totals['doadores'],
            'captadores': totals['captadores'],
            'media': float((totals['total'] or 0) / max(totals['count'], 1)),
        },
        'coordenadores': coordenadores,
        'cidades': cidades,
    })


# ─── Drill-down: detalhes por cidade ────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doacoes_city_detail(request, slug):
    """Detalhamento de doações de uma cidade."""
    from apps.geography.models import City
    city = get_object_or_404(City, slug=slug)
    periodo = request.query_params.get('periodo', 'total')

    paid_qs = Donation.objects.filter(
        captador__isnull=False,
        captador__contact__city=city,
    ).filter(Q(pix_status='paid') | Q(is_verified=True))
    paid_qs = _filtrar_por_periodo(paid_qs, periodo)

    totals = paid_qs.aggregate(
        total=Sum('amount'),
        count=Count('id'),
        doadores=Count('donor_cpf', distinct=True),
    )

    # Captadores da cidade
    captadores = list(
        paid_qs
        .values(
            captador_id=models_F('captador__id'),
            nome=models_F('captador__contact__full_name'),
            tipo=models_F('captador__tipo'),
        )
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )
    for c in captadores:
        c['total'] = float(c['total'] or 0)

    return Response({
        'city': {'slug': city.slug, 'name': city.name},
        'totals': {
            'total': float(totals['total'] or 0),
            'count': totals['count'],
            'doadores': totals['doadores'],
        },
        'captadores': captadores,
    })


# ─── Stats gerais da rede ────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rede_stats(request):
    """Estatísticas gerais da rede de captação."""
    total_captadores = Captador.objects.filter(is_active=True).count()
    total_coordenadores = Captador.objects.filter(is_active=True, tipo='coordenador').count()
    total_apoiadores = Captador.objects.filter(is_active=True, tipo='apoiador').count()

    paid_qs = Donation.objects.filter(
        captador__isnull=False,
    ).filter(Q(pix_status='paid') | Q(is_verified=True))

    totals = paid_qs.aggregate(
        total=Sum('amount'),
        count=Count('id'),
        doadores=Count('donor_cpf', distinct=True),
    )

    return Response({
        'captadores': total_captadores,
        'coordenadores': total_coordenadores,
        'apoiadores': total_apoiadores,
        'total_arrecadado': float(totals['total'] or 0),
        'total_doacoes': totals['count'],
        'total_doadores': totals['doadores'],
    })
