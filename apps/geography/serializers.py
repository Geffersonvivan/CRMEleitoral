from rest_framework import serializers
from .models import MacroRegion, Region, City, Neighborhood, ElectoralZone


class MacroRegionSerializer(serializers.ModelSerializer):
    regions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MacroRegion
        fields = ['id', 'name', 'slug', 'population', 'color', 'regions_count']


class RegionListSerializer(serializers.ModelSerializer):
    macro_region_name = serializers.CharField(source='macro_region.name', read_only=True)
    cities_count = serializers.IntegerField(read_only=True)
    contacts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Region
        fields = [
            'id', 'name', 'full_name', 'slug', 'macro_region', 'macro_region_name',
            'population', 'meta_votes', 'color', 'cities_count', 'contacts_count'
        ]


class RegionDetailSerializer(serializers.ModelSerializer):
    macro_region_name = serializers.CharField(source='macro_region.name', read_only=True)
    geojson = serializers.JSONField(read_only=True)

    class Meta:
        model = Region
        fields = '__all__'


class CityListSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = City
        fields = [
            'id', 'name', 'slug', 'ibge_code', 'region', 'region_name',
            'population', 'registered_voters', 'mayor_name', 'mayor_party',
            'num_vereadores', 'num_vereadores_pl', 'votes_sorgatto_2022', 'meta_votes'
        ]


class NeighborhoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood
        fields = ['id', 'name', 'slug', 'population', 'meta_votes']


class CityDetailSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)
    macro_region_name = serializers.CharField(source='region.macro_region.name', read_only=True)
    neighborhoods = NeighborhoodSerializer(many=True, read_only=True)

    class Meta:
        model = City
        fields = '__all__'


class ElectoralZoneSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = ElectoralZone
        fields = '__all__'
