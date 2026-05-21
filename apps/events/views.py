from rest_framework import viewsets
from apps.accounts.mixins import TerritoryFilterMixin
from .models import Event
from .serializers import EventSerializer


class EventViewSet(TerritoryFilterMixin, viewsets.ModelViewSet):
    queryset = Event.objects.select_related('city', 'region', 'organizer').all()
    serializer_class = EventSerializer
    filterset_fields = ['event_type', 'city', 'region']
    search_fields = ['title']
