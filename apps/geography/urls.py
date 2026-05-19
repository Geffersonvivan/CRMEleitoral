from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MacroRegionViewSet, RegionViewSet, CityViewSet

app_name = 'geography'

router = DefaultRouter()
router.register(r'macro-regions', MacroRegionViewSet, basename='macro-region')
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'cities', CityViewSet, basename='city')

urlpatterns = [
    path('', include(router.urls)),
]
