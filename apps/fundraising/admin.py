from django.contrib import admin
from .models import Donation, Expense


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'amount', 'date', 'method', 'is_verified')
    list_filter = ('method', 'is_verified', 'date')
    search_fields = ('donor__full_name', 'receipt_number')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'category', 'approved_by')
    list_filter = ('category', 'date')
    search_fields = ('description',)
