from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, CompanyPartnerViewSet, TagViewSet

app_name = 'contacts'

router = DefaultRouter()
router.register(r'', ContactViewSet, basename='contact')
router.register(r'companies', CompanyPartnerViewSet, basename='company')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
