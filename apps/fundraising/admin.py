from django.contrib import admin
from .models import Donation, Expense, Captador, SolicitacaoResgate


@admin.register(Captador)
class CaptadorAdmin(admin.ModelAdmin):
    list_display = ('contact', 'tipo', 'slug', 'get_region', 'total_arrecadado', 'is_active')
    list_filter = ('tipo', 'is_active', 'contact__region')
    search_fields = ('contact__full_name', 'contact__cpf', 'slug')
    raw_id_fields = ('contact', 'coordenador')
    readonly_fields = ('slug', 'saldo_disponivel', 'total_arrecadado')

    @admin.display(description='Região')
    def get_region(self, obj):
        return obj.contact.region.name if obj.contact.region else '-'


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'amount', 'date', 'method', 'pix_status', 'captador', 'is_verified')
    list_filter = ('method', 'is_verified', 'pix_status', 'date')
    search_fields = ('donor__full_name', 'donor_cpf', 'donor_name', 'receipt_number')
    raw_id_fields = ('donor', 'captador')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'category', 'approved_by')
    list_filter = ('category', 'date')
    search_fields = ('description',)


@admin.register(SolicitacaoResgate)
class SolicitacaoResgateAdmin(admin.ModelAdmin):
    list_display = ('captador', 'valor', 'status', 'data_pagamento')
    list_filter = ('status',)
    search_fields = ('captador__contact__full_name',)
    raw_id_fields = ('captador', 'aprovado_por')
