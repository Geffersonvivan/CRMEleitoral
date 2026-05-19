from rest_framework import serializers
from .models import Donation, Expense


class DonationSerializer(serializers.ModelSerializer):
    donor_name = serializers.CharField(source='donor.full_name', read_only=True, default='')

    class Meta:
        model = Donation
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
