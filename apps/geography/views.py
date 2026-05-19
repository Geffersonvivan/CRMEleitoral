from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import MacroRegion, Region, City, Neighborhood
from .serializers import (
    MacroRegionSerializer, RegionListSerializer, RegionDetailSerializer,
    CityListSerializer, CityDetailSerializer, NeighborhoodSerializer,
)


class MacroRegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MacroRegion.objects.annotate(
        regions_count=Count('regions'),
    ).order_by('name')
    serializer_class = MacroRegionSerializer
    lookup_field = 'slug'


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.select_related('macro_region').annotate(
        cities_count=Count('cities', distinct=True),
        contacts_count=Count('contacts', distinct=True),
    ).order_by('name')
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RegionDetailSerializer
        return RegionListSerializer

    @action(detail=True, methods=['get'])
    def cities(self, request, slug=None):
        region = self.get_object()
        cities = region.cities.all()
        serializer = CityListSerializer(cities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def geojson(self, request, slug=None):
        region = self.get_object()
        cities = region.cities.exclude(geojson__isnull=True)
        features = []
        for city in cities:
            if city.geojson:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'name': city.name,
                        'slug': city.slug,
                        'population': city.population,
                        'votes_2022': city.votes_sorgatto_2022,
                        'meta_votes': city.meta_votes,
                    },
                    'geometry': city.geojson,
                })
        return Response({
            'type': 'FeatureCollection',
            'features': features,
        })


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.select_related('region', 'region__macro_region')
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CityDetailSerializer
        return CityListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'retrieve':
            qs = qs.prefetch_related('neighborhoods')
        return qs

    @action(detail=True, methods=['get'])
    def neighborhoods(self, request, slug=None):
        city = self.get_object()
        neighborhoods = city.neighborhoods.all()
        serializer = NeighborhoodSerializer(neighborhoods, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def geojson(self, request, slug=None):
        city = self.get_object()
        return Response(city.geojson or {})
