from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationViewSet, ExpenseViewSet

app_name = 'fundraising'

router = DefaultRouter()
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'expenses', ExpenseViewSet, basename='expense')

urlpatterns = [
    path('', include(router.urls)),
]
