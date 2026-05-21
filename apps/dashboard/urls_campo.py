from django.urls import path
from .views_campo import (
    campo_home, campo_contato, campo_interacao,
    campo_checkin, campo_cidade,
    campo_home_api, campo_cidades_api, campo_cidade_detalhe_api,
    campo_cidade_por_gps_api, campo_eventos_checkin_api, campo_checkin_api,
)

# URLs de template (páginas HTML)
campo_pages = [
    path('', campo_home, name='campo-home'),
    path('contato/', campo_contato, name='campo-contato'),
    path('interacao/', campo_interacao, name='campo-interacao'),
    path('checkin/', campo_checkin, name='campo-checkin'),
    path('cidade/', campo_cidade, name='campo-cidade'),
]

# URLs de API (retornam JSON)
campo_api = [
    path('home/', campo_home_api, name='campo-api-home'),
    path('cidades/', campo_cidades_api, name='campo-api-cidades'),
    path('cidade/<int:pk>/', campo_cidade_detalhe_api, name='campo-api-cidade'),
    path('cidade-por-gps/', campo_cidade_por_gps_api, name='campo-api-gps'),
    path('eventos-checkin/', campo_eventos_checkin_api, name='campo-api-eventos'),
    path('checkin/<int:event_id>/', campo_checkin_api, name='campo-api-checkin'),
]
