from rest_framework import serializers
from django.db import transaction
from .models import Campaign, Task, Itinerary, ItineraryStop, Content


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True, default='',
    )
    city_name = serializers.CharField(
        source='city.name', read_only=True, default='',
    )
    region_name = serializers.CharField(
        source='region.name', read_only=True, default='',
    )
    region_color = serializers.CharField(
        source='region.color', read_only=True, default='#90a4ae',
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'


class CampaignSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'


class ItineraryStopSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    city_slug = serializers.CharField(source='city.slug', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True, default='')

    class Meta:
        model = ItineraryStop
        fields = '__all__'


class ItineraryStopWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ItineraryStop
        exclude = ['itinerary']


class ItinerarySerializer(serializers.ModelSerializer):
    stops = ItineraryStopSerializer(many=True, read_only=True)
    stops_input = ItineraryStopWriteSerializer(many=True, write_only=True, required=False)
    responsible_name = serializers.CharField(
        source='responsible.get_full_name', read_only=True, default='',
    )
    origin_city_name = serializers.CharField(
        source='origin_city.name', read_only=True, default='',
    )
    origin_city_slug = serializers.CharField(
        source='origin_city.slug', read_only=True, default='',
    )
    stops_count = serializers.IntegerField(source='stops.count', read_only=True)

    class Meta:
        model = Itinerary
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        stops_data = validated_data.pop('stops_input', [])
        regions = validated_data.pop('target_regions', [])
        itinerary = Itinerary.objects.create(**validated_data)
        if regions:
            itinerary.target_regions.set(regions)
        for stop in stops_data:
            stop.pop('id', None)
            ItineraryStop.objects.create(itinerary=itinerary, **stop)
        return itinerary

    @transaction.atomic
    def update(self, instance, validated_data):
        stops_data = validated_data.pop('stops_input', None)
        regions = validated_data.pop('target_regions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if regions is not None:
            instance.target_regions.set(regions)
        if stops_data is not None:
            existing_ids = set(instance.stops.values_list('id', flat=True))
            incoming_ids = set()
            for stop in stops_data:
                stop_id = stop.pop('id', None)
                if stop_id and stop_id in existing_ids:
                    ItineraryStop.objects.filter(id=stop_id).update(**stop)
                    incoming_ids.add(stop_id)
                else:
                    ItineraryStop.objects.create(itinerary=instance, **stop)
            # Remover paradas que nao vieram no payload
            instance.stops.exclude(id__in=incoming_ids).delete()
        return instance


class ItineraryListSerializer(serializers.ModelSerializer):
    responsible_name = serializers.CharField(
        source='responsible.get_full_name', read_only=True, default='',
    )
    origin_city_name = serializers.CharField(
        source='origin_city.name', read_only=True, default='',
    )
    stops_count = serializers.IntegerField(source='stops.count', read_only=True)
    cities_count = serializers.SerializerMethodField()

    class Meta:
        model = Itinerary
        fields = '__all__'

    def get_cities_count(self, obj):
        return obj.stops.values('city').distinct().count()


class ContentSerializer(serializers.ModelSerializer):
    responsible_name = serializers.CharField(
        source='responsible.get_full_name', read_only=True, default='',
    )
    task_title = serializers.CharField(
        source='task.title', read_only=True, default='',
    )
    city_name = serializers.CharField(
        source='task.city.name', read_only=True, default='',
    )

    class Meta:
        model = Content
        fields = '__all__'
