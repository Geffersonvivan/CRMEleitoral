from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ElectionViewSet, CandidateResultViewSet, VoteGoalViewSet

app_name = 'elections'

router = DefaultRouter()
router.register(r'elections', ElectionViewSet, basename='election')
router.register(r'results', CandidateResultViewSet, basename='result')
router.register(r'goals', VoteGoalViewSet, basename='goal')

urlpatterns = [
    path('', include(router.urls)),
]
