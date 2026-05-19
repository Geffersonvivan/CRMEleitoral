from django.urls import path
from .views import DashboardOverviewAPI, RegionDashboardAPI, CityDashboardAPI, StrategicAnalysisAPI, PLNetworkAPI, ZoneRankingAPI, VoteTransferAPI, NeighborDeputiesAPI, Elections2022API

app_name = 'dashboard'

urlpatterns = [
    path('overview/', DashboardOverviewAPI.as_view(), name='overview'),
    path('region/<slug:slug>/', RegionDashboardAPI.as_view(), name='region'),
    path('city/<slug:slug>/', CityDashboardAPI.as_view(), name='city'),
    path('strategic/', StrategicAnalysisAPI.as_view(), name='strategic'),
    path('pl-network/', PLNetworkAPI.as_view(), name='pl-network'),
    path('zone-ranking/', ZoneRankingAPI.as_view(), name='zone-ranking'),
    path('vote-transfer/', VoteTransferAPI.as_view(), name='vote-transfer'),
    path('neighbor-deputies/', NeighborDeputiesAPI.as_view(), name='neighbor-deputies'),
    path('elections-2022/', Elections2022API.as_view(), name='elections-2022'),
]
