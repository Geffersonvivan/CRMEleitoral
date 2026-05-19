from django.urls import path
from .views import dashboard_home, map_region_view, map_city_view

urlpatterns = [
    path('', dashboard_home, name='home'),
    path('regiao/<slug:slug>/', map_region_view, name='region-view'),
    path('cidade/<slug:slug>/', map_city_view, name='city-view'),
]
