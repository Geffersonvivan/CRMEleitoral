from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DonationViewSet, ExpenseViewSet, CaptadorViewSet,
    public_captador_info, public_criar_doacao,
    doacoes_map_data, doacoes_region_detail, doacoes_city_detail,
    rede_stats,
)

app_name = 'fundraising'

router = DefaultRouter()
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'captadores', CaptadorViewSet, basename='captador')

urlpatterns = [
    path('', include(router.urls)),
    # Públicos
    path('public/doar/<slug:slug>/', public_captador_info, name='public-captador-info'),
    path('public/doar/<slug:slug>/submit/', public_criar_doacao, name='public-criar-doacao'),
    # Mapa de doações
    path('map/doacoes/', doacoes_map_data, name='doacoes-map-data'),
    path('map/doacoes/regiao/<slug:slug>/', doacoes_region_detail, name='doacoes-region-detail'),
    path('map/doacoes/cidade/<slug:slug>/', doacoes_city_detail, name='doacoes-city-detail'),
    # Rede
    path('rede/stats/', rede_stats, name='rede-stats'),
]
