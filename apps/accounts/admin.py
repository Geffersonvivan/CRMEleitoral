from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'city', 'is_active_campaign')
    list_filter = ('role', 'is_active_campaign', 'region')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Campanha', {
            'fields': ('role', 'phone', 'whatsapp', 'city', 'region', 'photo', 'is_active_campaign', 'allowed_modules'),
        }),
    )
