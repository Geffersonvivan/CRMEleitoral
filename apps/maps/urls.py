from django.urls import path
from .views import StateMapAPI, RegionMapAPI, CityMapAPI, HeatmapAPI, StateCitiesMapAPI

app_name = 'maps'

urlpatterns = [
    path('state/', StateMapAPI.as_view(), name='state'),
    path('state-cities/', StateCitiesMapAPI.as_view(), name='state-cities'),
    path('region/<slug:slug>/', RegionMapAPI.as_view(), name='region'),
    path('city/<slug:slug>/', CityMapAPI.as_view(), name='city'),
    path('heatmap/<str:metric>/', HeatmapAPI.as_view(), name='heatmap'),
]
