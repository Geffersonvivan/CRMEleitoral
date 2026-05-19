from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, Count, Q
from django.utils import timezone
from .models import Campaign, Task, Itinerary, ItineraryStop, Content
from .serializers import (
    CampaignSerializer, TaskSerializer,
    ItinerarySerializer, ItineraryListSerializer, ItineraryStopSerializer,
    ContentSerializer,
)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.select_related(
        'task', 'task__city', 'responsible',
    ).order_by('-created_at')
    serializer_class = ContentSerializer
    filterset_fields = ['status', 'content_type', 'phase', 'task']
    search_fields = ['title', 'task__title']


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.prefetch_related(
        Prefetch('tasks', queryset=Task.objects.select_related('assigned_to', 'city', 'region')),
    )
    serializer_class = CampaignSerializer
    filterset_fields = ['status']
    search_fields = ['name']


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related(
        'campaign', 'assigned_to', 'city', 'region',
    ).order_by('-priority', 'due_date')
    serializer_class = TaskSerializer
    filterset_fields = ['campaign', 'phase', 'task_type', 'priority', 'assigned_to', 'city', 'region']
    search_fields = ['title', 'city__name']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Metricas do kanban para o header."""
        today = timezone.now().date()
        qs = self.get_queryset()

        region = request.query_params.get('region')
        city = request.query_params.get('city')
        if region:
            qs = qs.filter(region_id=region)
        if city:
            qs = qs.filter(city_id=city)

        return Response({
            'total': qs.count(),
            'by_phase': dict(qs.values_list('phase').annotate(c=Count('id')).order_by('phase')),
            'overdue': qs.exclude(phase='completed').filter(due_date__lt=today).count(),
            'cities_with_tasks': qs.values('city').distinct().count(),
            'cities_total': 295,
        })

    @action(detail=False, methods=['get'], url_path='region-tasks/(?P<region_slug>[^/.]+)')
    def region_tasks(self, request, region_slug=None):
        """Demandas por cidade para uma região específica."""
        today = timezone.now().date()
        from apps.geography.models import City

        cities = City.objects.filter(region__slug=region_slug).order_by('name')
        tasks = Task.objects.filter(city__region__slug=region_slug)

        open_by_city = dict(
            tasks.exclude(phase='completed')
            .values_list('city_id').annotate(c=Count('id'))
        )
        overdue_by_city = dict(
            tasks.exclude(phase='completed').filter(due_date__lt=today)
            .values_list('city_id').annotate(c=Count('id'))
        )
        completed_by_city = dict(
            tasks.filter(phase='completed')
            .values_list('city_id').annotate(c=Count('id'))
        )

        # Última visita (última task concluída com data)
        from django.db.models import Max
        last_visit_by_city = dict(
            tasks.filter(phase='completed', completed_at__isnull=False)
            .values_list('city_id').annotate(last=Max('completed_at'))
        )

        data = []
        for c in cities:
            data.append({
                'slug': c.slug,
                'name': c.name,
                'open': open_by_city.get(c.id, 0),
                'overdue': overdue_by_city.get(c.id, 0),
                'completed': completed_by_city.get(c.id, 0),
                'last_visit': str(last_visit_by_city[c.id]) if c.id in last_visit_by_city else None,
            })
        return Response(data)

    @action(detail=False, methods=['get'], url_path='map-status')
    def map_status(self, request):
        """Status de demandas por regiao para o modo Demandas do mapa."""
        today = timezone.now().date()
        from apps.geography.models import Region

        tasks = Task.objects.exclude(phase='completed')
        overdue_by_region = dict(
            tasks.filter(due_date__lt=today)
            .values_list('region_id').annotate(c=Count('id'))
        )
        near_due_by_region = dict(
            tasks.filter(
                due_date__gte=today,
                due_date__lte=today + timezone.timedelta(days=3),
            ).values_list('region_id').annotate(c=Count('id'))
        )
        active_by_region = dict(
            tasks.values_list('region_id').annotate(c=Count('id'))
        )

        data = []
        for r in Region.objects.all():
            overdue = overdue_by_region.get(r.id, 0)
            near = near_due_by_region.get(r.id, 0)
            active = active_by_region.get(r.id, 0)

            if overdue > 0:
                status = 'overdue'
            elif near > 0:
                status = 'near_due'
            elif active > 0:
                status = 'ok'
            else:
                status = 'empty'

            data.append({
                'slug': r.slug,
                'status': status,
                'active': active,
                'overdue': overdue,
            })
        return Response(data)


class ItineraryViewSet(viewsets.ModelViewSet):
    queryset = Itinerary.objects.select_related('responsible', 'origin_city').prefetch_related(
        Prefetch('stops', queryset=ItineraryStop.objects.select_related('city', 'task')),
    )
    filterset_fields = ['status']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ItineraryListSerializer
        return ItinerarySerializer

    @staticmethod
    def _city_coords(city):
        """Extrai lat/lng aproximado do geojson de uma cidade."""
        if not city or not city.geojson:
            return 0, 0
        geojson = city.geojson
        if geojson.get('type') == 'Polygon':
            coords = geojson.get('coordinates', [[]])[0]
            if coords:
                # Centroide aproximado
                lats = [c[1] for c in coords]
                lngs = [c[0] for c in coords]
                return sum(lats) / len(lats), sum(lngs) / len(lngs)
        return 0, 0

    @action(detail=False, methods=['get'], url_path='map-data')
    def map_data(self, request):
        """Dados dos roteiros para o modo Roteiros do mapa."""
        itineraries = self.get_queryset()
        show_completed = request.query_params.get('completed', 'false') == 'true'
        if not show_completed:
            itineraries = itineraries.exclude(status='completed')

        data = []
        for it in itineraries:
            stops = []

            # Cidade de origem como primeiro ponto
            if it.origin_city:
                lat, lng = self._city_coords(it.origin_city)
                if lat and lng:
                    stops.append({
                        'city_name': it.origin_city.name,
                        'city_slug': it.origin_city.slug,
                        'date': str(it.start_date),
                        'time': '',
                        'order': -1,
                        'task_title': '',
                        'is_overnight': False,
                        'is_origin': True,
                        'lat': lat,
                        'lng': lng,
                    })

            for stop in it.stops.select_related('city', 'task').order_by('date', 'order'):
                lat, lng = self._city_coords(stop.city)
                if lat and lng:
                    stops.append({
                        'city_name': stop.city.name,
                        'city_slug': stop.city.slug,
                        'date': str(stop.date),
                        'time': str(stop.scheduled_time) if stop.scheduled_time else '',
                        'order': stop.order,
                        'task_title': stop.task.title if stop.task else '',
                        'is_overnight': stop.is_overnight,
                        'is_origin': False,
                        'lat': lat,
                        'lng': lng,
                    })
            data.append({
                'id': it.id,
                'name': it.name,
                'status': it.status,
                'start_date': str(it.start_date),
                'end_date': str(it.end_date),
                'responsible': it.responsible.get_full_name() if it.responsible else '',
                'origin_city': it.origin_city.name if it.origin_city else '',
                'stops': stops,
            })
        return Response(data)
