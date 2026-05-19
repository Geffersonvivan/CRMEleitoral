from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True, default='')

    class Meta:
        model = Event
        fields = '__all__'
