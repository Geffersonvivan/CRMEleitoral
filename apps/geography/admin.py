from django.contrib import admin
from django.db.models import Count
from .models import MacroRegion, Region, City, Neighborhood, ElectoralZone


class RegionInline(admin.TabularInline):
    model = Region
    extra = 0
    fields = ('name', 'full_name', 'population', 'meta_votes', 'meta_doacoes')


@admin.register(MacroRegion)
class MacroRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'population', 'color')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RegionInline]


class CityInline(admin.TabularInline):
    model = City
    extra = 0
    fields = ('name', 'ibge_code', 'population', 'votes_sorgatto_2022', 'meta_votes')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_name', 'macro_region', 'population', 'meta_votes', 'meta_doacoes', 'cities_count')
    list_filter = ('macro_region',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'full_name')
    inlines = [CityInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(cities_count=Count('cities'))

    @admin.display(description='Cidades', ordering='cities_count')
    def cities_count(self, obj):
        return obj.cities_count


class NeighborhoodInline(admin.TabularInline):
    model = Neighborhood
    extra = 0
    fields = ('name', 'population', 'meta_votes')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'region', 'population', 'mayor_name', 'mayor_party',
        'num_vereadores', 'num_vereadores_pl', 'votes_sorgatto_2022', 'meta_votes'
    )
    list_filter = ('region', 'region__macro_region', 'mayor_party')
    search_fields = ('name', 'ibge_code', 'mayor_name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [NeighborhoodInline]


@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'population', 'meta_votes')
    list_filter = ('city__region',)
    search_fields = ('name', 'city__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ElectoralZone)
class ElectoralZoneAdmin(admin.ModelAdmin):
    list_display = ('zone_number', 'city', 'registered_voters')
    list_filter = ('city__region',)
    search_fields = ('zone_number', 'city__name')
