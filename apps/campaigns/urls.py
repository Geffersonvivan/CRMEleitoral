from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampaignViewSet, TaskViewSet, ItineraryViewSet, ContentViewSet

app_name = 'campaigns'

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'itineraries', ItineraryViewSet, basename='itinerary')
router.register(r'contents', ContentViewSet, basename='content')

urlpatterns = [
    path('', include(router.urls)),
]
