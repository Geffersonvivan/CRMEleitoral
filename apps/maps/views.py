from rest_framework.views import APIView
from rest_framework.response import Response
from apps.geography.models import MacroRegion, Region, City
from django.db.models import Count, Sum, Q


class StateMapAPI(APIView):
    """GeoJSON do estado com todas as regioes"""
    def get(self, request):
        regions = Region.objects.select_related('macro_region').annotate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
            total_apoiadores=Count('contacts', filter=Q(contacts__category='apoiador', contacts__is_active=True)),
            total_votes_2022=Sum('cities__votes_sorgatto_2022'),
            total_registered_voters=Sum('cities__registered_voters'),
        )
        features = []
        for region in regions:
            if region.geojson:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'name': region.name,
                        'full_name': region.full_name,
                        'slug': region.slug,
                        'macro_region': region.macro_region.name,
                        'population': region.population,
                        'color': region.color,
                        'meta_votes': region.meta_votes,
                        'total_contacts': region.total_contacts,
                        'total_apoiadores': region.total_apoiadores,
                        'total_votes_2022': region.total_votes_2022 or 0,
                        'registered_voters': region.total_registered_voters or 0,
                    },
                    'geometry': region.geojson,
                })
        return Response({
            'type': 'FeatureCollection',
            'features': features,
        })


class RegionMapAPI(APIView):
    """GeoJSON de uma regiao com suas cidades"""
    def get(self, request, slug):
        region = Region.objects.get(slug=slug)
        cities = region.cities.annotate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
        )
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
                        'registered_voters': city.registered_voters,
                        'meta_votes': city.meta_votes,
                        'total_contacts': city.total_contacts,
                        'mayor': city.mayor_name,
                    },
                    'geometry': city.geojson,
                })
        return Response({
            'type': 'FeatureCollection',
            'features': features,
            'region': {
                'name': region.name,
                'full_name': region.full_name,
                'population': region.population,
            }
        })


class CityMapAPI(APIView):
    """GeoJSON de uma cidade com seus bairros"""
    def get(self, request, slug):
        city = City.objects.get(slug=slug)
        neighborhoods = city.neighborhoods.annotate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
        )
        features = []
        for nb in neighborhoods:
            if nb.geojson:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'name': nb.name,
                        'slug': nb.slug,
                        'population': nb.population,
                        'meta_votes': nb.meta_votes,
                        'total_contacts': nb.total_contacts,
                    },
                    'geometry': nb.geojson,
                })
        return Response({
            'type': 'FeatureCollection',
            'features': features,
            'city': {
                'name': city.name,
                'population': city.population,
                'geojson': city.geojson,
            }
        })


class StateCitiesMapAPI(APIView):
    """GeoJSON de todas as cidades do estado (295 polígonos)"""
    def get(self, request):
        cities = City.objects.select_related('region').annotate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
        ).exclude(geojson__isnull=True)
        features = []
        for city in cities:
            if city.geojson:
                features.append({
                    'type': 'Feature',
                    'properties': {
                        'name': city.name,
                        'slug': city.slug,
                        'region_name': city.region.name,
                        'region_slug': city.region.slug,
                        'population': city.population,
                        'votes_2022': city.votes_sorgatto_2022,
                        'registered_voters': city.registered_voters,
                        'meta_votes': city.meta_votes,
                        'total_contacts': city.total_contacts,
                    },
                    'geometry': city.geojson,
                })
        return Response({
            'type': 'FeatureCollection',
            'features': features,
        })


class HeatmapAPI(APIView):
    """Dados para choropleth baseado em metrica"""
    def get(self, request, metric):
        regions = Region.objects.annotate(
            total_contacts=Count('contacts', filter=Q(contacts__is_active=True)),
            total_apoiadores=Count('contacts', filter=Q(contacts__category='apoiador', contacts__is_active=True)),
            total_votes_2022=Sum('cities__votes_sorgatto_2022'),
        )
        data = []
        for region in regions:
            value = 0
            if metric == 'contacts':
                value = region.total_contacts
            elif metric == 'apoiadores':
                value = region.total_apoiadores
            elif metric == 'votes_2022':
                value = region.total_votes_2022 or 0
            elif metric == 'meta_progress':
                if region.meta_votes > 0:
                    value = round((region.total_apoiadores / region.meta_votes) * 100, 2)
            elif metric == 'saturation':
                if region.population > 0:
                    value = round((region.total_apoiadores / region.population) * 100, 4)
            data.append({
                'slug': region.slug,
                'name': region.name,
                'value': value,
            })
        return Response(data)
