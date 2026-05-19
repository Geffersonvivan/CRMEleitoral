from rest_framework import serializers
from .models import Election, CandidateResult, VoteGoal


class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = '__all__'


class CandidateResultSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = CandidateResult
        fields = '__all__'


class VoteGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.FloatField(read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True, default=None)
    city_name = serializers.CharField(source='city.name', read_only=True, default=None)

    class Meta:
        model = VoteGoal
        fields = '__all__'
