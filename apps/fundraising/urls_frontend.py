from django.urls import path
from .views_frontend import captadores_page, rede_page

app_name = 'fundraising_frontend'

urlpatterns = [
    path('', captadores_page, name='captadores'),
    path('rede/', rede_page, name='rede'),
]
