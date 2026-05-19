from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Election, CandidateResult, VoteGoal
from .serializers import ElectionSerializer, CandidateResultSerializer, VoteGoalSerializer


class ElectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    filterset_fields = ['year', 'election_type']


class CandidateResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CandidateResult.objects.select_related('city', 'election').all()
    serializer_class = CandidateResultSerializer
    filterset_fields = ['election', 'city', 'party', 'is_sorgatto']
    search_fields = ['candidate_name', 'city__name']

    @action(detail=False, methods=['get'], url_path='city/(?P<city_slug>[^/.]+)')
    def by_city(self, request, city_slug=None):
        results = self.queryset.filter(city__slug=city_slug)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)


class VoteGoalViewSet(viewsets.ModelViewSet):
    queryset = VoteGoal.objects.select_related('macro_region', 'region', 'city', 'neighborhood').all()
    serializer_class = VoteGoalSerializer
    filterset_fields = ['level', 'election_year', 'region', 'city']
