from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Contact, CompanyPartner, Interaction, Tag


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 0
    fields = ('interaction_type', 'description', 'outcome', 'performed_by', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    list_display = (
        'full_name', 'category', 'engagement_level', 'city',
        'region', 'phone', 'whatsapp', 'party', 'is_active'
    )
    list_filter = ('category', 'engagement_level', 'region', 'party', 'is_active', 'tags')
    search_fields = ('full_name', 'nickname', 'cpf', 'email', 'phone', 'whatsapp')
    list_editable = ('category', 'engagement_level')
    raw_id_fields = ('city', 'region', 'neighborhood', 'referred_by')
    inlines = [InteractionInline]
    fieldsets = (
        ('Dados Pessoais', {
            'fields': (
                'full_name', 'nickname', 'cpf', 'birth_date',
                'email', 'phone', 'whatsapp', 'photo'
            ),
        }),
        ('Campanha', {
            'fields': (
                'category', 'engagement_level', 'party',
                'profession', 'referred_by', 'tags', 'is_active'
            ),
        }),
        ('Localizacao', {
            'fields': (
                'region', 'city', 'neighborhood',
                'street', 'number', 'complement', 'neighborhood_name', 'zip_code',
                'latitude', 'longitude'
            ),
        }),
        ('Eleitoral', {
            'fields': ('voter_registration', 'electoral_zone', 'electoral_section'),
        }),
        ('Observacoes', {
            'fields': ('notes',),
        }),
    )


@admin.register(CompanyPartner)
class CompanyPartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'sector', 'employees_count', 'partnership_type')
    list_filter = ('sector', 'city__region')
    search_fields = ('name', 'cnpj')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('contact', 'interaction_type', 'outcome', 'performed_by', 'created_at')
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('contact__full_name', 'description')
    raw_id_fields = ('contact', 'performed_by')
