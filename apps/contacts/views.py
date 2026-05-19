from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Prefetch, Q
from .models import Contact, CompanyPartner, Interaction, Tag
from .serializers import (
    ContactListSerializer, ContactDetailSerializer,
    CompanyPartnerSerializer, InteractionSerializer, TagSerializer,
)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.select_related('city', 'region').annotate(
        referrals_count=Count('referrals')
    ).order_by('full_name')
    filterset_fields = ['category', 'engagement_level', 'region', 'city', 'party', 'is_active']
    search_fields = ['full_name', 'nickname', 'email', 'phone', 'whatsapp']
    ordering_fields = ['full_name', 'created_at', 'engagement_level']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContactDetailSerializer
        return ContactListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'retrieve':
            qs = qs.prefetch_related(
                'tags',
                Prefetch(
                    'interactions',
                    queryset=Interaction.objects.select_related('performed_by'),
                ),
            )
        return qs

    @action(detail=True, methods=['get', 'post'])
    def interactions(self, request, pk=None):
        contact = self.get_object()
        if request.method == 'POST':
            serializer = InteractionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(contact=contact, performed_by=request.user)
            return Response(serializer.data, status=201)
        interactions = contact.interactions.select_related('performed_by').all()
        serializer = InteractionSerializer(interactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats/by-region')
    def stats_by_region(self, request):
        stats = Contact.objects.filter(is_active=True).values(
            'region__name', 'region__slug'
        ).annotate(
            total=Count('id'),
            coordenadores=Count('id', filter=Q(category__startswith='coordenador')),
            apoiadores=Count('id', filter=Q(category='apoiador')),
            parceiros=Count('id', filter=Q(category='parceiro')),
        ).order_by('region__name')
        return Response(list(stats))

    @action(detail=False, methods=['get'], url_path='stats/by-category')
    def stats_by_category(self, request):
        stats = Contact.objects.filter(is_active=True).values('category').annotate(
            total=Count('id')
        ).order_by('-total')
        return Response(list(stats))


class CompanyPartnerViewSet(viewsets.ModelViewSet):
    queryset = CompanyPartner.objects.select_related('city', 'contact_person').all()
    serializer_class = CompanyPartnerSerializer
    filterset_fields = ['city', 'sector']
    search_fields = ['name', 'cnpj']


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
