from rest_framework import viewsets
from .models import Donation, Expense
from .serializers import DonationSerializer, ExpenseSerializer


class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.select_related('donor').all()
    serializer_class = DonationSerializer
    filterset_fields = ['method', 'is_verified']


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    filterset_fields = ['category']
