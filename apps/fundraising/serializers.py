from rest_framework import serializers
from .models import Donation, Expense, Captador


class DonationSerializer(serializers.ModelSerializer):
    donor_display = serializers.CharField(source='donor.full_name', read_only=True, default='')
    captador_name = serializers.CharField(
        source='captador.contact.full_name', read_only=True, default=''
    )

    class Meta:
        model = Donation
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'


class CaptadorSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_cpf = serializers.CharField(source='contact.cpf', read_only=True, default='')
    contact_phone = serializers.CharField(source='contact.phone', read_only=True, default='')
    contact_city = serializers.CharField(source='contact.city.name', read_only=True, default='')
    contact_region = serializers.CharField(source='contact.region.name', read_only=True, default='')
    contact_region_slug = serializers.CharField(
        source='contact.region.slug', read_only=True, default=''
    )
    contact_photo = serializers.ImageField(source='contact.photo', read_only=True, default=None)
    coordenador_name = serializers.CharField(
        source='coordenador.contact.full_name', read_only=True, default=''
    )
    link = serializers.SerializerMethodField()
    qrcode_url = serializers.SerializerMethodField()
    total_doacoes = serializers.SerializerMethodField()

    class Meta:
        model = Captador
        fields = [
            'id', 'contact', 'contact_name', 'contact_cpf', 'contact_phone',
            'contact_city', 'contact_region', 'contact_region_slug', 'contact_photo',
            'tipo', 'coordenador', 'coordenador_name',
            'slug', 'link', 'qrcode_url', 'qrcode_image',
            'is_active', 'saldo_disponivel', 'total_arrecadado',
            'total_doacoes', 'created_at',
        ]
        read_only_fields = ('slug', 'qrcode_image', 'saldo_disponivel', 'total_arrecadado')

    def get_link(self, obj):
        return obj.get_link()

    def get_qrcode_url(self, obj):
        if obj.qrcode_image:
            return obj.qrcode_image.url
        return ''

    def get_total_doacoes(self, obj):
        return obj.doacoes_captadas.filter(pix_status='paid').count()


class CaptadorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Captador
        fields = ('contact', 'tipo', 'coordenador')


class PublicDoacaoSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)
    nome = serializers.CharField(max_length=255)
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
