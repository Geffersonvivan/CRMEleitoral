from rest_framework import serializers
from .models import Contact, CompanyPartner, Interaction, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class InteractionSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name', read_only=True
    )

    class Meta:
        model = Interaction
        fields = '__all__'


class ContactListSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    referrals_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id', 'full_name', 'nickname', 'category', 'engagement_level',
            'city', 'city_name', 'region', 'region_name',
            'phone', 'whatsapp', 'party', 'is_active', 'referrals_count'
        ]


class ContactDetailSerializer(serializers.ModelSerializer):
    interactions = InteractionSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    referrals_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Contact
        fields = '__all__'


class CompanyPartnerSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = CompanyPartner
        fields = '__all__'
